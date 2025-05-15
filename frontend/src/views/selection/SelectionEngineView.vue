// --- START OF FILE frontend/src/views/selection/SelectionEngineView.vue ---
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
              <el-tag v-if="strategy.tags && strategy.tags.length" :type="getTagType(strategy.tags[0])" size="small" style="margin-left: 8px;">{{ strategy.tags[0] }}</el-tag>
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
      <el-form label-width="160px" label-position="left"> {/* 调整了label-width */}
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
            style="width: calc(100% - 50px);" 
          />
          <span style="margin-left: 10px; width: 40px; display: inline-block;">{{ param.unit || '' }}</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="generatePool" :loading="loadingPool">应用参数并筛选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="selectionPool.length > 0 || loadingPool" class="results-area" shadow="never"> 
      <template #header>
        <div class="card-header">
          <span>{{ selectedStrategy?.name }} - 筛选结果</span> 
          <span style="font-size: 12px; color: #909399; margin-left: 10px;"> (数据更新于: {{ poolTimestamp || 'N/A' }})</span>
        </div>
      </template>
      <el-table :data="selectionPool" stripe style="width: 100%" v-loading="loadingPool">
        <el-table-column prop="name" label="标的名称" width="180" fixed="left" />
        <el-table-column prop="ts_code" label="代码" width="120" />

        {/* 动量质量双引擎的特定列 */}
        <template v-if="selectedStrategyId === 'value_momentum'">
          <el-table-column prop="roe" label="ROE(%)" sortable >
            <template #default="scope">
              {{ scope.row.roe !== null && scope.row.roe !== undefined ? (scope.row.roe * 100).toFixed(2) + '%' : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="pb" label="市净率(PB)" sortable >
            <template #default="scope">
              {{ scope.row.pb !== null && scope.row.pb !== undefined ? scope.row.pb.toFixed(2) : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="momentum_6m" label="6月动量(%)" sortable>
            <template #default="scope">
              {{ scope.row.momentum_6m !== null && scope.row.momentum_6m !== undefined ? (scope.row.momentum_6m * 100).toFixed(2) + '%' : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="composite_score" label="综合得分" width="120" sortable>
              <template #default="scope">
                  <el-progress :percentage="scope.row.composite_score || 0" :stroke-width="8" :color="getScoreColor(scope.row.composite_score)" />
              </template>
          </el-table-column>
        </template>

        {/* 简单价值筛选的特定列 */}
        <template v-if="selectedStrategyId === 'simple_value_screen'">
          <el-table-column prop="pe_ttm" label="市盈率(TTM)" sortable >
            <template #default="scope">
              {{ scope.row.pe_ttm !== null && scope.row.pe_ttm !== undefined ? scope.row.pe_ttm.toFixed(2) : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="pb" label="市净率(PB)" sortable >
            <template #default="scope">
             {{ scope.row.pb !== null && scope.row.pb !== undefined ? scope.row.pb.toFixed(2) : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="dividend_yield_ratio" label="股息率(%)" sortable >
             <template #default="scope">
              {{ scope.row.dividend_yield_ratio !== null && scope.row.dividend_yield_ratio !== undefined ? (scope.row.dividend_yield_ratio * 100).toFixed(2) + '%' : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="total_mv" label="总市值(亿元)" sortable >
             <template #default="scope">
              {{ scope.row.total_mv !== null && scope.row.total_mv !== undefined ? scope.row.total_mv.toFixed(2) : 'N/A' }}
            </template>
          </el-table-column>
        </template>

        <el-table-column label="操作" width="180" fixed="right"> 
          <template #default="scope">
            <el-button size="small" @click="viewDetails(scope.row)">详情</el-button>
            <el-button size="small" type="primary" plain @click="addToTiming(scope.row)" style="margin-left: 5px;">择时分析</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
     <el-empty v-if="!loadingPool && selectionPool.length === 0 && selectedStrategyId" description="暂无符合条件的标的" class="results-area" />
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'; // 移除了 watch，添加了 computed
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { fetchSelectionStrategies, generateSelectionPool } from '@/api';

const router = useRouter();

const presetStrategies = ref([]);
const selectedStrategy = ref(null);
const selectedStrategyId = ref(''); // 保持 string 类型
const editableParams = reactive({});

const selectionPool = ref([]);
const loadingPool = ref(false);
const poolTimestamp = ref('');

// 一个简单的函数来根据标签内容决定类型，可以根据需要扩展
const getTagType = (tag) => {
  if (tag === '价值') return 'success';
  if (tag === '动量') return 'warning';
  if (tag === '质量') return 'info';
  return 'primary'; // 默认
};


onMounted(async () => {
  try {
    const response = await fetchSelectionStrategies();
    presetStrategies.value = response.data;
    // 可以在这里默认选中第一个策略，如果需要的话
    // if (presetStrategies.value.length > 0) {
    //   selectStrategy(presetStrategies.value[0]);
    // }
  } catch (error) {
    ElMessage.error('获取选品策略列表失败');
    console.error(error);
  }
});

const selectStrategy = (strategy) => {
  // 清理旧策略的参数（如果 editableParams 中存在）
  for (const key in editableParams) {
    delete editableParams[key];
  }

  selectedStrategy.value = strategy;
  selectedStrategyId.value = strategy.id; // 正确赋值
  
  if (strategy.params) {
    strategy.params.forEach(param => {
      editableParams[param.name] = param.value;
    });
  }
  selectionPool.value = [];
  poolTimestamp.value = '';
};

const generatePool = async () => {
  if (!selectedStrategy.value) {
    ElMessage.warning('请先选择一个策略');
    return;
  }
  loadingPool.value = true;
  selectionPool.value = []; // 在请求开始前清空，避免显示旧数据
  try {
    const requestData = {
      strategy_id: selectedStrategy.value.id,
      params: { ...editableParams }
    };
    const response = await generateSelectionPool(requestData);
    if (response.data && response.data.items) {
      selectionPool.value = response.data.items;
      poolTimestamp.value = response.data.timestamp ? new Date(response.data.timestamp).toLocaleString() : 'N/A';
      if (selectionPool.value.length === 0) {
        ElMessage.info('未筛选到符合条件的标的');
      } else {
        ElMessage.success('标的池已更新');
      }
    } else {
      ElMessage.error('获取标的池数据格式不正确');
      selectionPool.value = []; // 确保数据格式不对时也清空
    }
  } catch (error) {
    ElMessage.error(`生成标的池失败: ${error.response?.data?.detail || error.message}`);
    console.error(error);
    selectionPool.value = []; // 出错时清空
  } finally {
    loadingPool.value = false;
  }
};

const getScoreColor = (score) => {
  if (!score) return '#F56C6C'; // 如果分数不存在或为0，默认为红色或灰色
  if (score >= 80) return '#67C23A';
  if (score >= 60) return '#E6A23C';
  return '#F56C6C';
};

const viewDetails = (row) => {
  console.log('View details for:', row);
  // router.push(`/stock/${row.ts_code}`);
};

const addToTiming = (row) => {
  console.log('Add to timing analysis:', row);
  router.push({ name: 'TimingEngine', query: { stockCode: row.ts_code, stockName: row.name } }); // 可以传递更多信息
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
  height: 100%; /* 让卡片等高 */
  display: flex;
  flex-direction: column;
}
.strategy-card .el-card__header { /* Element Plus v2.x 的 header 类名 */
 flex-shrink: 0;
}
.strategy-card .el-card__body {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.strategy-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,.1);
}
.strategy-card.is-selected {
  border-color: var(--el-color-primary); /* 使用 Element Plus 变量 */
  box-shadow: 0 0 0 2px var(--el-color-primary-light-5); /* 使用 Element Plus 变量 */
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
  line-height: 1.5;
  flex-grow: 1; /* 让描述占据更多空间 */
  /* min-height: 3em; 移除固定高度，让flex布局处理 */
}
.performance-summary small {
  font-size: 12px;
  color: #909399;
}
.params-adjustment-area, .results-area {
  margin-top: 20px;
}
.results-area .el-table {
  margin-top: 10px;
}
.el-empty { /* 空状态样式 */
  margin-top: 20px;
}
</style>
// --- END OF FILE frontend/src/views/selection/SelectionEngineView.vue ---