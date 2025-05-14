// frontend/src/views/DashboardView.vue
<template>
  <div class="dashboard-view">
    <el-page-header title="主仪表盘" content="市场概览及投资机会" @back="goBack" v-if="showPageHeader" />
    <el-divider v-if="showPageHeader" />

    <!-- 顶部概览卡片 -->
    <el-row :gutter="20" class="summary-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover">
          <div class="card-content">
            <div class="card-label">总资产 (CNY)</div>
            <div class="card-value">{{ summaryData.totalAssets.toLocaleString() }}</div>
            <div :class="['card-sub-value', summaryData.dailyPnlPercent >= 0 ? 'positive' : 'negative']">
              当日盈亏: {{ summaryData.dailyPnl.toLocaleString() }} ({{ summaryData.dailyPnlPercent.toFixed(2) }}%)
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover">
          <div class="card-content">
            <div class="card-label">持仓标的数量</div>
            <div class="card-value">{{ summaryData.holdingCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover">
          <div class="card-content">
            <div class="card-label">市场风险评估</div>
            <el-tag :type="getRiskTagType(summaryData.marketRisk)" size="large">{{ summaryData.marketRisk }}</el-tag>
            <el-tooltip content="基于VIX指数和市场波动性评估" placement="top">
              <el-icon style="margin-left: 5px; cursor: pointer;"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover">
          <div class="card-content">
            <div class="card-label">待处理信号</div>
            <div class="card-value">{{ summaryData.pendingSignals }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 核心操作信号聚合卡片 -->
    <el-row :gutter="20" class="action-signal-cards">
      <el-col :xs="24" :sm="8">
        <el-card shadow="always" style="background-color: #f0f9eb;">
          <template #header>
            <div class="card-header">
              <span><el-icon><SuccessFilled /></el-icon> 买入信号</span>
            </div>
          </template>
          <div>{{ coreSignals.buySignals }} 个标的符合买入条件</div>
          <el-button type="primary" plain size="small" @click="viewSignalDetails('buy')" style="margin-top: 10px;">查看详情</el-button>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="always" style="background-color: #fdf6ec;">
          <template #header>
            <div class="card-header">
              <span><el-icon><WarningFilled /></el-icon> 观察信号</span>
            </div>
          </template>
          <div>{{ coreSignals.watchSignals }} 个标的进入观察区间</div>
          <el-button type="warning" plain size="small" @click="viewSignalDetails('watch')" style="margin-top: 10px;">查看详情</el-button>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="always" style="background-color: #fef0f0;">
          <template #header>
            <div class="card-header">
              <span><el-icon><CircleCloseFilled /></el-icon> 卖出信号</span>
            </div>
          </template>
          <div>{{ coreSignals.sellSignals }} 个持仓触发退出条件</div>
          <el-button type="danger" plain size="small" @click="viewSignalDetails('sell')" style="margin-top: 10px;">查看详情</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 最新投资机会 -->
      <el-col :xs="24" :lg="12">
        <el-card class="box-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>最新投资机会</span>
              <el-tooltip content="数据每小时更新一次" placement="top">
                <el-icon style="cursor: pointer;"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <el-table :data="latestOpportunities" style="width: 100%" height="250" empty-text="暂无最新机会">
            <el-table-column label="信号" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.type === 'buy' ? 'success' : 'warning'" size="small">
                  {{ scope.row.type === 'buy' ? '买入' : '观察' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="标的名称/代码" />
            <el-table-column prop="reason" label="信号简述" show-overflow-tooltip />
            <el-table-column prop="price" label="当前价格" width="100" />
          </el-table>
        </el-card>
      </el-col>

      <!-- 市场趋势图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="box-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>市场趋势</span>
               <el-tooltip content="上证指数 vs VIX指数 (模拟)" placement="top">
                <el-icon style="cursor: pointer;"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div ref="marketTrendChart" style="width: 100%; height: 250px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 持仓表现 -->
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-card class="box-card" shadow="never">
                <template #header>
                    <div class="card-header">
                        <span>我的持仓</span>
                        <el-button type="primary" plain size="small" @click="goToHoldings">管理持仓</el-button>
                    </div>
                </template>
                <el-table :data="holdingPerformance" style="width: 100%" height="200" empty-text="暂无持仓">
                    <el-table-column prop="name" label="标的名称/代码" />
                    <el-table-column prop="currentPrice" label="当前价格" />
                    <el-table-column prop="pnlPercent" label="持仓收益(%)">
                        <template #default="scope">
                            <span :class="scope.row.pnlPercent >= 0 ? 'positive-text' : 'negative-text'">
                                {{ scope.row.pnlPercent.toFixed(2) }}%
                            </span>
                        </template>
                    </el-table-column>
                    <el-table-column prop="exitStatus" label="止盈/止损状态">
                         <template #default="scope">
                            <el-tag :type="getExitStatusTagType(scope.row.exitStatus)" size="small">
                                {{ scope.row.exitStatus }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作">
                        <template #default="scope">
                            <el-button size="small" @click="viewHoldingDetail(scope.row)">详情</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-card>
        </el-col>
    </el-row>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts/core'; // 按需引入或全部引入
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
// 引入 Element Plus Icons (确保已全局注册或在此处导入)
import { QuestionFilled, SuccessFilled, WarningFilled, CircleCloseFilled, InfoFilled } from '@element-plus/icons-vue';


// 注册 ECharts 组件
echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer]);

const router = useRouter();
const showPageHeader = ref(false); // 根据需要控制 PageHeader 是否显示

// 模拟数据
const summaryData = reactive({
  totalAssets: 368549.28,
  dailyPnl: 2135.67,
  dailyPnlPercent: 0.58,
  holdingCount: 8,
  marketRisk: '中等风险', // '低风险', '中等风险', '高风险'
  pendingSignals: 5,
});

const coreSignals = reactive({
  buySignals: 3,
  watchSignals: 5,
  sellSignals: 2,
});

const latestOpportunities = ref([
  { type: 'buy', name: '贵州茅台 (600519)', reason: '波动压缩突破，均线支撑', price: 1789.00 },
  { type: 'buy', name: '创业板ETF (159915)', reason: '估值历史低位，RSI超卖', price: 2.457 },
  { type: 'watch', name: '宁德时代 (300750)', reason: '波动性降低，等待方向', price: 128.45 },
]);

const holdingPerformance = ref([
    { name: '贵州茅台 (600519)', currentPrice: 1789.00, pnlPercent: 12.31, exitStatus: '移动止盈中' },
    { name: '立讯精密 (002475)', currentPrice: 26.53, pnlPercent: -5.24, exitStatus: '机器学习预警' },
]);


const marketTrendChart = ref(null); // 用于 ECharts 实例的 ref
let myChart = null;

const initMarketTrendChart = () => {
  if (marketTrendChart.value && !myChart) { //确保DOM元素存在且图表未初始化
    myChart = echarts.init(marketTrendChart.value);
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['上证指数', 'VIX指数']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月'] // 模拟X轴数据
      },
      yAxis: [
        {
          type: 'value',
          name: '上证指数',
          position: 'left',
        },
        {
          type: 'value',
          name: 'VIX指数',
          position: 'right',
          axisLine: { show: true },
        }
      ],
      series: [
        {
          name: '上证指数',
          type: 'line',
          smooth: true,
          data: [3400, 3420, 3380, 3450, 3500, 3480, 3520, 3550, 3600] // 模拟上证数据
        },
        {
          name: 'VIX指数',
          type: 'line',
          smooth: true,
          yAxisIndex: 1,
          data: [20, 22, 18, 25, 23, 20, 17, 15, 19] // 模拟VIX数据
        }
      ]
    };
    myChart.setOption(option);
  }
};

onMounted(() => {
  // 可以在这里从API获取真实数据来填充 summaryData, coreSignals 等
  // fetchDashboardData().then(data => { ... });
  nextTick(() => { // 确保DOM渲染完成后再初始化ECharts
    initMarketTrendChart();
  });
});

// 窗口大小改变时重绘图表
window.addEventListener('resize', () => {
  if (myChart) {
    myChart.resize();
  }
});


const getRiskTagType = (riskLevel) => {
  if (riskLevel === '低风险') return 'success';
  if (riskLevel === '中等风险') return 'warning';
  if (riskLevel === '高风险') return 'danger';
  return 'info';
};

const getExitStatusTagType = (status) => {
    if (status.includes('预警') || status.includes('止损')) return 'danger';
    if (status.includes('止盈')) return 'success';
    return 'primary';
};


const viewSignalDetails = (signalType) => {
  ElMessage.info(`查看 ${signalType} 类型信号详情 (功能待实现)`);
  // router.push(`/signals/${signalType}`);
  if (signalType === 'buy' || signalType === 'watch') {
    router.push({ name: 'TimingEngine' }); // 跳转到择时引擎页面
  } else if (signalType === 'sell') {
    router.push({ name: 'ExitEngine' }); // 跳转到退出引擎页面
  }
};

const goToHoldings = () => {
    router.push({ name: 'ExitEngine' }); // 跳转到退出引擎/持仓管理页面
};

const viewHoldingDetail = (row) => {
    ElMessage.info(`查看持仓 ${row.name} 详情 (功能待实现)`);
};


const goBack = () => {
  router.back();
};

</script>

<style scoped>
.dashboard-view {
  padding: 20px;
}
.el-page-header {
  margin-bottom: 20px;
}
.summary-cards .el-col,
.action-signal-cards .el-col {
  margin-bottom: 20px;
}
.card-content {
  text-align: center;
}
.card-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.card-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
  color: #303133;
}
.card-sub-value {
  font-size: 12px;
}
.positive {
  color: #67c23a;
}
.negative {
  color: #f56c6c;
}
.positive-text {
  color: #67c23a;
}
.negative-text {
  color: #f56c6c;
}
.action-signal-cards .el-card {
  text-align: center;
}
.action-signal-cards .card-header span {
  font-weight: bold;
}
.action-signal-cards .el-icon {
  vertical-align: middle;
  margin-right: 5px;
}
.box-card {
  height: 100%; /* 确保卡片在Row中高度一致，如果需要的话 */
}
.box-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>