// frontend/src/views/timing/TimingEngineView.vue
<template>
  <div class="timing-engine-view">
    <el-page-header title="黄金窗口 · 择时引擎" content="把握精准买入/观察时机" @back="goBack" />
    <el-divider />

    <el-row :gutter="20" class="strategy-selection-area">
      <el-col :span="8" v-for="strategy in presetTimingStrategies" :key="strategy.id">
        <el-card
          shadow="hover"
          :class="{ 'strategy-card': true, 'is-selected': selectedTimingStrategyId === strategy.id }"
          @click="selectTimingStrategy(strategy)"
        >
          <template #header>
            <div class="card-header">
              <span>{{ strategy.name }}</span>
              <el-tag v-if="strategy.tags && strategy.tags.length" type="info" size="small" style="margin-left: 8px;">{{ strategy.tags[0] }}</el-tag>
            </div>
          </template>
          <p class="strategy-description">{{ strategy.description }}</p>
           <div v-if="strategy.historical_performance_summary" class="performance-summary">
            <small>胜率: {{ strategy.historical_performance_summary.win_rate }} | 盈亏比: {{ strategy.historical_performance_summary.profit_loss_ratio }}</small>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="selectedTimingStrategy" class="params-adjustment-area" shadow="never">
      <template #header>
        <div class="card-header">
          <span>参数调整 - {{ selectedTimingStrategy.name }}</span>
        </div>
      </template>
      <el-alert
        title="提示：择时信号通常基于「智能灯塔」选品结果或您的自选股池。"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 20px;"
      />
      <el-form label-width="150px" label-position="left">
        <el-form-item
          v-for="param in selectedTimingStrategy.params"
          :key="param.name"
          :label="param.description || param.name"
        >
          <el-slider
            v-model="editableTimingParams[param.name]"
            :min="param.min_value"
            :max="param.max_value"
            :step="param.step"
            show-input
            style="width: 80%;"
          />
          <span style="margin-left: 10px;">{{ param.unit || '' }}</span>
        </el-form-item>
        <el-form-item label="应用标的池">
            <el-select
                v-model="selectedStockPoolSource"
                placeholder="选择标的来源"
                style="width: 300px; margin-right: 10px;"
            >
                <el-option label="来自选品引擎结果" value="selection_engine"></el-option>
                <el-option label="我的自选股" value="my_watchlist"></el-option>
                <!-- <el-option label="全市场扫描 (耗时较长)" value="all_market"></el-option> -->
            </el-select>
            <el-button type="primary" @click="generateTimingSignals" :loading="loadingSignals">生成择时信号</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="timingSignals.length > 0" class="results-area" shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ selectedTimingStrategy.name }} - 择时信号</span>
           <span style="font-size: 12px; color: #909399; margin-left: 10px;"> (数据更新于: {{ signalsTimestamp || 'N/A' }})</span>
        </div>
      </template>
      <el-table :data="timingSignals" stripe style="width: 100%" v-loading="loadingSignals">
        <el-table-column prop="name" label="标的名称" width="180" />
        <el-table-column prop="ts_code" label="代码" width="120" />
        <el-table-column prop="current_price" label="当前价格" width="100" />
        <el-table-column prop="signal_type" label="信号类型" width="150" />
        <el-table-column prop="signal_strength" label="信号强度" width="120">
           <template #default="scope">
                <el-progress :percentage="scope.row.signal_strength * 100 || 0" :stroke-width="8" :color="getSignalStrengthColor(scope.row.signal_strength)" />
            </template>
        </el-table-column>
        <el-table-column prop="trigger_time" label="触发时间" width="160" />
        <el-table-column label="建议操作" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.suggestion === '买入' ? 'success' : (scope.row.suggestion === '观察' ? 'warning' : 'info')" size="small">
              {{ scope.row.suggestion }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" @click="viewSignalDetails(scope.row)">详情</el-button>
            <!-- <el-button size="small" type="primary" plain @click="addToExitWatch(scope.row)" v-if="scope.row.suggestion === '买入'">模拟买入</el-button> -->
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { fetchTimingStrategies, generateTimingSignals as apiGenerateTimingSignals } from '@/api'; // 假设 API 服务已封装
// import { useAppStore } from '@/store/app'; // 如果有全局状态管理选品结果

const router = useRouter();
const route = useRoute();
// const appStore = useAppStore();

const presetTimingStrategies = ref([]);
const selectedTimingStrategy = ref(null);
const selectedTimingStrategyId = ref('');
const editableTimingParams = reactive({});

const selectedStockPoolSource = ref('selection_engine'); // 'selection_engine', 'my_watchlist'

const timingSignals = ref([]);
const loadingSignals = ref(false);
const signalsTimestamp = ref('');

// 从选品引擎传递过来的标的 (示例，实际应从store或更可靠的机制获取)
const stocksFromSelection = computed(() => {
    // 简单示例，实际中选品结果可能更复杂，并存储在Pinia中
    // return appStore.selectionPoolResult || [];
    // 或者，如果从路由参数传递了一个特定股票
    if (route.query.stockCode) {
        return [{ ts_code: route.query.stockCode, name: `来自关注 (${route.query.stockCode})` }];
    }
    return []; // 默认空
});

onMounted(async () => {
  try {
    const response = await fetchTimingStrategies();
    presetTimingStrategies.value = response.data || [ // 模拟数据，如果API未实现
        { id: 'rsi_crossover', name: 'RSI超卖反弹', description: '利用RSI指标判断短期超卖并寻找反弹机会。', params: [{name: 'rsi_period', value: 14, min_value:5, max_value:30, unit:'周期'}, {name: 'rsi_buy_threshold', value: 30, min_value:10, max_value:40, unit:''}], tags: ['技术指标'], historical_performance_summary: {win_rate: "60%", profit_loss_ratio: "1.8"}},
        { id: 'bb_breakout', name: '波动率压缩突破', description: '在波动率收缩后，捕捉价格向上突破布林带上轨的信号。', params: [{name: 'bb_period', value: 20, min_value:10, max_value:60, unit:'周期'}, {name: 'bb_std_dev', value: 2, min_value:1, max_value:3, unit:'标准差'}], tags: ['波动率'], historical_performance_summary: {win_rate: "55%", profit_loss_ratio: "2.1"}},
    ];
  } catch (error) {
    ElMessage.error('获取择时策略列表失败');
    console.error(error);
  }
});

const selectTimingStrategy = (strategy) => {
  selectedTimingStrategy.value = strategy;
  selectedTimingStrategyId.value = strategy.id;
  if (strategy.params) {
    strategy.params.forEach(param => {
      editableTimingParams[param.name] = param.value;
    });
  }
  timingSignals.value = [];
  signalsTimestamp.value = '';
};

const generateTimingSignals = async () => {
  if (!selectedTimingStrategy.value) {
    ElMessage.warning('请先选择一个择时策略');
    return;
  }

  let stockCodesToProcess = [];
  if (selectedStockPoolSource.value === 'selection_engine') {
      // stockCodesToProcess = stocksFromSelection.value.map(s => s.ts_code); // 假设选品结果在 stocksFromSelection
      // 模拟：如果没有从选品引擎获取到，给个提示或使用默认列表
      if (stocksFromSelection.value.length === 0) {
          ElMessage.info('当前无选品引擎结果，将使用示例标的池。');
          stockCodesToProcess = ["600519.SH", "000001.SZ"]; // 示例
      } else {
          stockCodesToProcess = stocksFromSelection.value.map(s => s.ts_code);
      }
  } else if (selectedStockPoolSource.value === 'my_watchlist') {
      // stockCodesToProcess = appStore.myWatchlist.map(s => s.ts_code); // 假设自选股在Pinia Store中
      ElMessage.info('「我的自选股」功能待实现，将使用示例标的池。');
      stockCodesToProcess = ["000300.SH", "399006.SZ"]; // 示例
  }

  if (stockCodesToProcess.length === 0 && selectedStockPoolSource.value !== 'all_market') {
      ElMessage.warning('标的池为空，无法生成择时信号。');
      return;
  }


  loadingSignals.value = true;
  try {
    const requestData = {
      // selection_strategy_id: appStore.selectedSelectionStrategyId, // 可能需要传递选品策略ID和参数
      // selection_params: appStore.selectedSelectionParams,
      timing_strategy_id: selectedTimingStrategy.value.id,
      timing_params: { ...editableTimingParams },
      stock_codes: stockCodesToProcess, // 传递标的代码列表给后端
    };
    // const response = await apiGenerateTimingSignals(requestData);
    // timingSignals.value = response.data.signals;
    // signalsTimestamp.value = new Date(response.data.timestamp).toLocaleString();

    // 模拟API返回
    await new Promise(resolve => setTimeout(resolve, 1000));
    timingSignals.value = [
        { name: '贵州茅台', ts_code: '600519.SH', current_price: 1780.50, signal_type: 'RSI金叉', signal_strength: 0.75, trigger_time: new Date().toLocaleString(), suggestion: '买入'},
        { name: '平安银行', ts_code: '000001.SZ', current_price: 10.50, signal_type: '均线支撑', signal_strength: 0.60, trigger_time: new Date().toLocaleString(), suggestion: '观察'},
    ];
    signalsTimestamp.value = new Date().toLocaleString();

    ElMessage.success('择时信号已更新');
  } catch (error) {
    ElMessage.error(`生成择时信号失败: ${error.response?.data?.detail || error.message}`);
    console.error(error);
  } finally {
    loadingSignals.value = false;
  }
};

const getSignalStrengthColor = (strength) => {
  if (strength >= 0.8) return '#67C23A'; // 绿色
  if (strength >= 0.6) return '#E6A23C'; // 黄色
  return '#F56C6C'; // 红色
};

const viewSignalDetails = (row) => {
  console.log('View signal details for:', row);
  // 弹窗显示更详细的信号信息，图表等
  ElMessage.info(`查看 ${row.name} 的详细择时信号 (功能待实现)`);
};

const goBack = () => {
  router.back();
};
</script>

<style scoped>
.timing-engine-view {
  padding: 20px;
}
.el-page-header {
  margin-bottom: 20px;
}
.strategy-selection-area .el-col {
  margin-bottom: 20px;
}
.strategy-card {
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}
.strategy-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,.1);
}
.strategy-card.is-selected {
  border-color: #409EFF;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.6);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.strategy-description {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  min-height: 3em; /* 保证几行的高度 */
}
.performance-summary small {
  font-size: 12px;
  color: #909399;
}
.params-adjustment-area, .results-area {
  margin-top: 20px;
}
</style>