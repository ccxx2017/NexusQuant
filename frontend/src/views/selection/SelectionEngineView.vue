<template>
  <div class="selection-engine-view">
    <el-page-header title="智能灯塔 · 选品引擎" content="解决「买什么」的核心问题" @back="goBack" />
    <el-divider />

    <el-row :gutter="20" class="strategy-selection-area">
      <el-col :span="8" v-for="strategy in presetStrategies" :key="strategy.id">
        <el-card
          shadow="hover"
          :class="{ 'strategy-card': true, 'is-selected': selectedStrategyId === strategy.id }"
          @click="selectStrategy(strategy)"
        >
          <template #header>
            <div class="card-header">
              <span>{{ strategy.name }}</span>
              <el-tag v-if="strategy.tags && strategy.tags.length" type="success" size="small" style="margin-left: 8px;">{{ strategy.tags[0] }}</el-tag>
            </div>
          </template>
          <p class="strategy-description">{{ strategy.description }}</p>
          <div v-if="strategy.historical_performance_summary" class="performance-summary">
            <small>年化: {{ strategy.historical_performance_summary.annual_return }} | 回撤: {{ strategy.historical_performance_summary.max_drawdown }}</small>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="selectedStrategy" class="params-adjustment-area" shadow="never">
      <template #header>
        <div class="card-header">
          <span>参数调整 - {{ selectedStrategy.name }}</span>
        </div>
      </template>
      <el-form label-width="150px" label-position="left">
        <el-form-item
          v-for="param in selectedStrategy.params"
          :key="param.name"
          :label="param.description || param.name"
        >
          <el-slider
            v-model="editableParams[param.name]"
            :min="param.min_value"
            :max="param.max_value"
            :step="param.step"
            show-input
            style="width: 80%;"
          />
          <span style="margin-left: 10px;">{{ param.unit || '' }}</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="generatePool" :loading="loadingPool">应用参数并筛选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="selectionPool.length > 0" class="results-area" shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ selectedStrategy.name }} - 筛选结果</span>
          <span style="font-size: 12px; color: #909399; margin-left: 10px;"> (数据更新于: {{ poolTimestamp || 'N/A' }})</span>
        </div>
      </template>
      <el-table :data="selectionPool" stripe style="width: 100%" v-loading="loadingPool">
        <el-table-column prop="name" label="标的名称" width="180" />
        <el-table-column prop="ts_code" label="代码" width="120" />
        <el-table-column prop="roe" label="ROE(%)" sortable />
        <el-table-column prop="pb" label="市净率(PB)" sortable />
        <el-table-column prop="momentum_6m" label="6月动量(%)" sortable>
          <template #default="scope">
            {{ (scope.row.momentum_6m * 100).toFixed(2) }}%
          </template>
        </el-table-column>
        <el-table-column prop="composite_score" label="综合得分" width="120" sortable>
            <template #default="scope">
                <el-progress :percentage="scope.row.composite_score || 0" :stroke-width="8" :color="getScoreColor(scope.row.composite_score)" />
            </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="viewDetails(scope.row)">详情</el-button>
            <el-button size="small" type="primary" plain @click="addToTiming(scope.row)">择时分析</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { fetchSelectionStrategies, generateSelectionPool } from '@/api'; // 假设 API 服务已封装

const router = useRouter();

const presetStrategies = ref([]);
const selectedStrategy = ref(null);
const selectedStrategyId = ref('');
const editableParams = reactive({});

const selectionPool = ref([]);
const loadingPool = ref(false);
const poolTimestamp = ref('');

onMounted(async () => {
  try {
    const response = await fetchSelectionStrategies();
    presetStrategies.value = response.data;
  } catch (error) {
    ElMessage.error('获取选品策略列表失败');
    console.error(error);
  }
});

const selectStrategy = (strategy) => {
  selectedStrategy.value = strategy;
  selectedStrategyId.value = strategy.id;
  // 初始化可编辑参数
  if (strategy.params) {
    strategy.params.forEach(param => {
      editableParams[param.name] = param.value; // 使用默认值初始化
    });
  }
  selectionPool.value = []; // 清空旧结果
  poolTimestamp.value = '';
};

const generatePool = async () => {
  if (!selectedStrategy.value) {
    ElMessage.warning('请先选择一个策略');
    return;
  }
  loadingPool.value = true;
  try {
    const requestData = {
      strategy_id: selectedStrategy.value.id,
      params: { ...editableParams } // 发送当前调整后的参数
    };
    const response = await generateSelectionPool(requestData);
    selectionPool.value = response.data.items;
    poolTimestamp.value = new Date(response.data.timestamp).toLocaleString();
    ElMessage.success('标的池已更新');
  } catch (error) {
    ElMessage.error(`生成标的池失败: ${error.response?.data?.detail || error.message}`);
    console.error(error);
  } finally {
    loadingPool.value = false;
  }
};

const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'; // 绿色
  if (score >= 60) return '#E6A23C'; // 黄色
  return '#F56C6C'; // 红色
};

const viewDetails = (row) => {
  console.log('View details for:', row);
  // router.push(`/stock/${row.ts_code}`); // 导航到详情页
};

const addToTiming = (row) => {
  console.log('Add to timing analysis:', row);
  // 可以用Pinia store传递给择时模块，或通过路由参数
  // appStore.addStockToTimingWatchlist(row);
  router.push({ name: 'TimingEngine', query: { stockCode: row.ts_code } });
};

const goBack = () => {
  router.back();
};
</script>

<style scoped>
.selection-engine-view {
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