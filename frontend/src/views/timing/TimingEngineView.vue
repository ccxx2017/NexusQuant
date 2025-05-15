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
       <el-col :span="24" v-if="presetTimingStrategies.length === 0 && !loadingStrategies">
         <el-empty description="未能从后端加载择时策略列表，请检查后端服务或网络连接。" />
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
      <el-form label-width="180px" label-position="left">
        <template v-for="param in selectedTimingStrategy.params" :key="param.name">
          <!-- 明确检查 param.type === 'boolean' 或者 param.name 来决定是否使用 el-switch -->
          <el-form-item
            v-if="param.type === 'boolean' || (selectedTimingStrategy.id === 'ma_golden_cross' && param.name === 'enable_volume_filter')"
            :label="param.description || param.name"
          >
            <el-switch
              v-model="editableTimingParams[param.name]"
              :active-value="true"
              :inactive-value="false"
            />
          </el-form-item>

          <!-- 条件渲染成交量相关参数：仅当是均线策略且成交量过滤开关打开时显示 -->
          <el-form-item
            v-else-if="selectedTimingStrategy.id === 'ma_golden_cross' && (param.name === 'volume_avg_days' || param.name === 'volume_multiple')"
            :label="`${param.description || param.name}`"
            v-show="editableTimingParams['enable_volume_filter'] === true"
          >
            <el-slider
              v-model="editableTimingParams[param.name]"
              :min="param.min_value"
              :max="param.max_value"
              :step="param.step"
              show-input
              style="width: calc(80% - 20px); margin-right: 5px;"
            />
            <span style="margin-left: 10px; display: inline-block; min-width: 20px;">{{ param.unit || '' }}</span>
          </el-form-item>

          <!-- 其他数字类型的参数，使用 el-slider (确保 param.value 是数字类型) -->
          <el-form-item
            v-else-if="typeof editableTimingParams[param.name] === 'number'"
            :label="`${param.description || param.name}`"
          >
            <el-slider
              v-model="editableTimingParams[param.name]"
              :min="param.min_value"
              :max="param.max_value"
              :step="param.step"
              show-input
              style="width: calc(80% - 20px); margin-right: 5px;"
            />
             <span style="margin-left: 10px; display: inline-block; min-width: 20px;">{{ param.unit || '' }}</span>
          </el-form-item>

          <!-- 可选：为其他未知类型的参数提供一个简单的文本输入作为回退 -->
          <el-form-item
            v-else
            :label="param.description || param.name"
          >
            <el-input v-model="editableTimingParams[param.name]" placeholder="参数值" style="width: calc(80% - 20px); margin-right: 5px;" />
             <span style="margin-left: 10px; display: inline-block; min-width: 20px;">{{ param.unit || '' }}</span>
          </el-form-item>

        </template>

        <el-form-item label="应用标的池">
            <el-select
                v-model="selectedStockPoolSource"
                placeholder="选择标的来源"
                style="width: 300px; margin-right: 10px;"
            >
                <el-option label="来自选品引擎结果 (模拟)" value="selection_engine"></el-option>
                <el-option label="我的自选股 (手动输入)" value="my_watchlist"></el-option>
            </el-select>
            <el-button type="primary" @click="generateTimingSignals" :loading="loadingSignals">生成择时信号</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="selectedTimingStrategy" class="results-area" shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ selectedTimingStrategy.name }} - 择时信号</span>
           <span style="font-size: 12px; color: #909399; margin-left: 10px;"> (数据更新于: {{ signalsTimestamp || 'N/A' }})</span>
        </div>
      </template>

      <div v-if="loadingSignals" style="text-align: center; padding: 20px;">
        <el-icon class="is-loading" :size="26"><Loading /></el-icon>
        <p>正在加载信号...</p>
      </div>
      <div v-else>
        <el-table v-if="timingSignals.length > 0" :data="timingSignals" stripe style="width: 100%">
          <el-table-column prop="name" label="标的名称" width="180" />
          <el-table-column prop="ts_code" label="代码" width="120" />
          <el-table-column prop="trigger_price" label="触发价格" width="100" />
          <el-table-column prop="signal_type" label="信号类型" width="200" />
          <el-table-column prop="signal_strength" label="信号强度" width="120">
            <template #default="scope">
                  <el-progress :percentage="scope.row.signal_strength * 100 || 0" :stroke-width="8" :color="getSignalStrengthColor(scope.row.signal_strength)" />
              </template>
          </el-table-column>
          <el-table-column prop="trigger_date" label="触发日期" width="160" />
          <el-table-column label="建议操作" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.suggestion === '买入' ? 'success' : (scope.row.suggestion === '观察' ? 'warning' : (scope.row.suggestion === '风险' || scope.row.suggestion === '暂不操作' ? 'info' : 'primary'))" size="small">
                {{ scope.row.suggestion }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button size="small" @click="viewSignalDetails(scope.row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loadingSignals && timingSignals.length === 0 && showNoSignalMessage" description="根据当前参数，未发现符合条件的择时信号" style="margin-top: 20px;"/>
      </div>
    </el-card>
    <el-card v-else-if="!selectedTimingStrategy && !loadingStrategies" class="results-area" shadow="never" style="text-align: center; padding: 50px;">
        <el-empty description="请先在上方选择一个择时策略，或检查策略列表是否加载成功" />
    </el-card>
     <el-card v-if="loadingStrategies" class="results-area" shadow="never" style="text-align: center; padding: 50px;">
        <el-icon class="is-loading" :size="26"><Loading /></el-icon>
        <p>正在加载策略列表...</p>
    </el-card>

  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import { fetchTimingStrategies, generateTimingSignals as apiGenerateTimingSignals } from '@/api';

const router = useRouter();
const route = useRoute();

const presetTimingStrategies = ref([]);
const selectedTimingStrategy = ref(null);
const selectedTimingStrategyId = ref('');
const editableTimingParams = reactive({});
const loadingStrategies = ref(true); // 新增：用于表示策略列表是否正在加载

const selectedStockPoolSource = ref('selection_engine');
const manualInputTickers = ref('');

const timingSignals = ref([]);
const loadingSignals = ref(false);
const signalsTimestamp = ref('');
const showNoSignalMessage = ref(false);

// 模拟的选品引擎结果
const simulatedSelectionPool = ref([
  { ts_code: '000001.SZ', name: '平安银行 (模拟选品)' },
  { ts_code: '600519.SH', name: '贵州茅台 (模拟选品)' },
  { ts_code: '000725.SZ', name: '京东方A (模拟选品)' },
  { ts_code: '300750.SZ', name: '宁德时代 (模拟选品)' },
]);


const getVolumeFilterParam = (paramName, defaultValue) => {
  if (!selectedStrategy.value || selectedStrategy.value.id !== 'ma_cross') {
    return defaultValue;
  }
  const param = currentStrategyParams.value.find(p => p.name === paramName);
  return param ? param.value : defaultValue;
};

onMounted(async () => {
  loadingStrategies.value = true;
  try {
    const response = await fetchTimingStrategies();
    if (response.data && response.data.length > 0) {
        presetTimingStrategies.value = response.data;
        if (presetTimingStrategies.value.length > 0) {
            selectTimingStrategy(presetTimingStrategies.value[0]); // 默认选中第一个
        }
    } else {
        ElMessage.warning('未能从后端获取择时策略列表，请检查后端服务。');
        presetTimingStrategies.value = []; // 清空，让 el-empty 显示
    }
  } catch (error) {
    ElMessage.error('获取择时策略列表失败');
    console.error("Error fetching timing strategies:", error);
    presetTimingStrategies.value = []; // 出错时也清空
  } finally {
    loadingStrategies.value = false;
  }
});

const selectTimingStrategy = (strategy) => {
  selectedTimingStrategy.value = strategy;
  selectedTimingStrategyId.value = strategy.id;
  for (const key in editableTimingParams) {
    delete editableTimingParams[key];
  }
  if (strategy.params) {
    strategy.params.forEach(param => {
      editableTimingParams[param.name] = param.value;
    });
  }
  timingSignals.value = [];
  signalsTimestamp.value = '';
  showNoSignalMessage.value = false;
};

const generateTimingSignals = async () => {
  if (!selectedTimingStrategy.value) {
    ElMessage.warning('请先选择一个择时策略');
    return;
  }

  let target_tickers_to_process = [];

  if (selectedStockPoolSource.value === 'selection_engine') {
    if (simulatedSelectionPool.value.length > 0) {
      target_tickers_to_process = simulatedSelectionPool.value.map(s => s.ts_code);
      ElMessage.info(`使用模拟的“选品引擎结果”标的池 (${target_tickers_to_process.length}只股票)`);
    } else {
      ElMessage.info('模拟的“选品引擎结果”为空，请尝试手动输入标的。');
       try {
            const { value } = await ElMessageBox.prompt('请输入股票代码，多个用英文逗号隔开 (例如：000001.SZ,600519.SH)', '手动输入标的池', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                inputValue: manualInputTickers.value,
                inputPattern: /^[0-9A-Za-z.,SHszSZ\s]*$/,
                inputErrorMessage: '股票代码格式不正确'
            });
            manualInputTickers.value = value;
            target_tickers_to_process = value.split(',').map(s => s.trim()).filter(s => s);
          } catch (e) {
            ElMessage.info('取消手动输入');
            return;
          }
    }
  } else if (selectedStockPoolSource.value === 'my_watchlist') {
    ElMessage.info('「我的自选股」功能需要您手动输入标的。');
    try {
        const { value } = await ElMessageBox.prompt('请输入股票代码，多个用英文逗号隔开 (例如：000001.SZ,600519.SH)', '手动输入标的池', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            inputValue: manualInputTickers.value,
            inputPattern: /^[0-9A-Za-z.,SHszSZ\s]*$/,
            inputErrorMessage: '股票代码格式不正确'
        });
        manualInputTickers.value = value;
        target_tickers_to_process = value.split(',').map(s => s.trim()).filter(s => s);
      } catch (e) {
        ElMessage.info('取消手动输入');
        return;
      }
  }

  if (target_tickers_to_process.length === 0) {
      ElMessage.warning('标的池为空，无法生成择时信号。');
      return;
  }

  loadingSignals.value = true;
  timingSignals.value = [];
  showNoSignalMessage.value = false;

  try {
    const requestData = {
      target_tickers: target_tickers_to_process,
      strategy_id: selectedTimingStrategy.value.id,
      params: { ...editableTimingParams },
    };
    
    console.log("Requesting timing signals with data:", JSON.stringify(requestData, null, 2));

    const response = await apiGenerateTimingSignals(requestData);

    if (response.data && response.data.signals) {
        timingSignals.value = response.data.signals.map(signal => {
            let suggestion = '关注';
            if (signal.signal_type === "RSI_OVERSOLD_TURN_UP" || signal.signal_type === "MA_GOLDEN_CROSS") {
                suggestion = '买入';
            } else if (signal.signal_type === "RSI_IN_OVERSOLD_ZONE") {
                suggestion = '观察';
            }else if (signal.signal_type === "MA_DEATH_CROSS") {
                suggestion = '风险'; // 死叉可以标记为风险或观察卖出
            }
            return { ...signal, suggestion: suggestion };
        });
        signalsTimestamp.value = response.data.data_timestamp ? new Date(response.data.data_timestamp).toLocaleString() : new Date().toLocaleString();
        if (timingSignals.value.length > 0) {
            ElMessage.success(`成功获取 ${timingSignals.value.length} 条择时信号`);
        } else {
            ElMessage.info('未发现符合条件的择时信号'); // 如果信号数组为空，给一个更明确的 info 提示
        }
    } else {
        ElMessage.warning('后端未返回有效的信号数据');
        timingSignals.value = [];
    }

  } catch (error) {
    ElMessage.error(`生成择时信号失败: ${error.response?.data?.detail || error.message}`);
    console.error("Error generating timing signals:", error);
    timingSignals.value = [];
  } finally {
    loadingSignals.value = false;
    showNoSignalMessage.value = true;
  }
};

const getSignalStrengthColor = (strength) => {
  if (!strength) return '#F56C6C'; // 处理 strength 可能为 undefined 或 null 的情况
  if (strength >= 0.7) return '#67C23A';
  if (strength >= 0.4) return '#E6A23C';
  return '#F56C6C';
};

const viewSignalDetails = (row) => {
  ElMessageBox.alert(
    `<pre>${JSON.stringify(row, null, 2)}</pre>`,
    `信号详情: ${row.name || 'N/A'} (${row.ts_code || 'N/A'})`,
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭',
      width: '60%', // 可以调整弹窗宽度
    }
  );
};

const goBack = () => {
  router.back();
};

watch(() => route.query.stockCode, (newStockCode) => {
    if (newStockCode && selectedTimingStrategy.value) {
        ElMessageBox.confirm(`检测到关注标的 ${newStockCode}，是否立即为其生成择时信号?`, '提示', {
            confirmButtonText: '立即生成',
            cancelButtonText: '稍后手动',
            type: 'info'
        }).then(() => {
            selectedStockPoolSource.value = 'my_watchlist';
            manualInputTickers.value = newStockCode;
            generateTimingSignals();
        }).catch(() => {});
    }
}, { immediate: true });

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
  height: 100%; /* 让卡片高度一致 */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
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
  flex-grow: 1; /* 让描述区域占据剩余空间 */
  min-height: 4em; /* 保证几行的高度 */
}
.performance-summary small {
  font-size: 12px;
  color: #909399;
}
.params-adjustment-area, .results-area {
  margin-top: 20px;
}
.el-icon.is-loading {
  animation: rotating 2s linear infinite;
}

</style>