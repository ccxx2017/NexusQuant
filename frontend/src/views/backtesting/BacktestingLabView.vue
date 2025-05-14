// frontend/src/views/backtesting/BacktestingLabView.vue
<template>
  <div class="backtesting-lab-view">
    <el-page-header title="策略实验室 · 回测" content="验证您的三位一体策略组合" @back="goBack" />
    <el-divider />

    <el-row :gutter="20">
      <!-- 左侧：策略配置与回测参数 -->
      <el-col :xs="24" :md="8">
        <el-card shadow="never" class="config-panel">
          <template #header>
            <div class="card-header">
              <span>回测配置</span>
            </div>
          </template>

          <el-form :model="backtestForm" ref="backtestFormRef" label-position="top">
            <el-tabs v-model="activeConfigTab">
              <el-tab-pane label="策略组合" name="strategies">
                <el-form-item label="1. 选品策略">
                  <el-select v-model="backtestForm.selection_strategy_id" placeholder="选择选品策略" style="width:100%;" @change="loadStrategyParams('selection')">
                    <el-option v-for="s in availableSelectionStrategies" :key="s.id" :label="s.name" :value="s.id" />
                  </el-select>
                  <!-- TODO: 显示并允许修改选品策略参数 (可弹窗或展开) -->
                </el-form-item>
                <el-form-item label="2. 择时策略">
                  <el-select v-model="backtestForm.timing_strategy_id" placeholder="选择择时策略" style="width:100%;" @change="loadStrategyParams('timing')">
                     <el-option v-for="s in availableTimingStrategies" :key="s.id" :label="s.name" :value="s.id" />
                  </el-select>
                  <!-- TODO: 显示并允许修改择时策略参数 -->
                </el-form-item>
                <el-form-item label="3. 退出策略">
                  <el-select v-model="backtestForm.exit_strategy_id" placeholder="选择退出策略" style="width:100%;" @change="loadStrategyParams('exit')">
                     <el-option v-for="s in availableExitStrategies" :key="s.id" :label="s.name" :value="s.id" />
                  </el-select>
                  <!-- TODO: 显示并允许修改退出策略参数 -->
                </el-form-item>
                 <el-alert title="提示" type="info" show-icon :closable="false" style="margin-bottom:10px;">
                    详细策略参数可在各引擎模块配置，此处将使用您在对应模块的最新配置或默认配置进行回测。后续可增加回测专用参数调整功能。
                </el-alert>
              </el-tab-pane>

              <el-tab-pane label="回测设置" name="settings">
                <el-form-item label="回测区间" prop="date_range">
                  <el-date-picker
                    v-model="backtestForm.backtest_config.date_range"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    style="width:100%;"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
                <el-form-item label="初始资金" prop="initial_cash">
                  <el-input-number v-model="backtestForm.backtest_config.initial_cash" :min="10000" :step="10000" style="width:100%;" />
                </el-form-item>
                <el-form-item label="手续费率 (万分之)" prop="commission_bps">
                  <el-input-number v-model="backtestForm.backtest_config.commission_bps" :min="0" :max="100" :step="0.1" style="width:100%;" />
                </el-form-item>
                <el-form-item label="对比基准" prop="benchmark_ticker">
                  <el-select v-model="backtestForm.backtest_config.benchmark_ticker" placeholder="选择基准指数" style="width:100%;">
                    <el-option label="沪深300 (000300.SH)" value="000300.SH" />
                    <el-option label="中证500 (000905.SH)" value="000905.SH" />
                    <el-option label="创业板指 (399006.SZ)" value="399006.SZ" />
                    <el-option label="无基准对比" value="" />
                  </el-select>
                </el-form-item>
                <el-form-item label="目标标的池 (可选)">
                    <el-input
                        v-model="backtestForm.target_tickers_str"
                        type="textarea"
                        :rows="3"
                        placeholder="输入股票代码，用逗号分隔，如 600519.SH,000001.SZ。如果留空，则由选品策略动态生成。"
                    />
                </el-form-item>
              </el-tab-pane>
            </el-tabs>

            <el-form-item style="margin-top: 20px;">
              <el-button type="primary" @click="runBacktest" :loading="isBacktesting" style="width: 100%;">
                <el-icon style="margin-right: 5px;"><VideoPlay /></el-icon>
                运行回测
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：回测结果展示 -->
      <el-col :xs="24" :md="16">
        <el-card shadow="never" class="results-panel">
          <template #header>
            <div class="card-header">
              <span>回测结果</span>
              <el-button type="text" @click="showResultDetails = !showResultDetails" v-if="backtestResult">
                {{ showResultDetails ? '收起详情' : '展开详情' }}
              </el-button>
            </div>
          </template>

          <el-empty description="请先配置策略并运行回测" v-if="!backtestResult && !isBacktesting" />
          <div v-loading="isBacktesting" element-loading-text="回测运行中，请稍候..." style="min-height: 200px;">
            <div v-if="backtestResult">
              <!-- 结果摘要弹窗式卡片 (简化) -->
              <el-descriptions title="回测绩效摘要" :column="2" border size="small" style="margin-bottom: 20px;">
                <el-descriptions-item label="总收益率">{{ (backtestResult.performance_summary.total_return * 100).toFixed(2) }}%</el-descriptions-item>
                <el-descriptions-item label="年化收益率">{{ (backtestResult.performance_summary.annual_return * 100).toFixed(2) }}%</el-descriptions-item>
                <el-descriptions-item label="最大回撤">{{ (backtestResult.performance_summary.max_drawdown * 100).toFixed(2) }}%</el-descriptions-item>
                <el-descriptions-item label="夏普比率">{{ backtestResult.performance_summary.sharpe_ratio.toFixed(2) }}</el-descriptions-item>
                <el-descriptions-item label="胜率">{{ (backtestResult.performance_summary.win_rate * 100).toFixed(2) }}%</el-descriptions-item>
                <el-descriptions-item label="盈亏比">{{ backtestResult.performance_summary.profit_loss_ratio.toFixed(2) }}</el-descriptions-item>
              </el-descriptions>

              <div ref="equityCurveChartRef" style="width: 100%; height: 350px; margin-bottom: 20px;"></div>

              <el-collapse v-model="activeCollapseNames" v-if="showResultDetails">
                <el-collapse-item title="本次回测配置" name="1">
                  <pre style="font-size: 12px; white-space: pre-wrap; word-break: break-all;">{{ JSON.stringify(backtestResult.config_used, null, 2) }}</pre>
                </el-collapse-item>
                <el-collapse-item title="交易统计 (示例)" name="2">
                  <p>总交易次数: {{ backtestResult.trades_summary?.total_trades || 'N/A' }}</p>
                  <!-- 更多交易统计信息 -->
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { runBacktest as apiRunBacktest, fetchSelectionStrategies, fetchTimingStrategies, fetchExitStrategies } from '@/api';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent, DataZoomComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { VideoPlay } from '@element-plus/icons-vue'; // 确保导入

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, DataZoomComponent, CanvasRenderer]);

const router = useRouter();
const activeConfigTab = ref('strategies');

// --- 策略列表 ---
const availableSelectionStrategies = ref([]);
const availableTimingStrategies = ref([]);
const availableExitStrategies = ref([]);

const backtestFormRef = ref(null);
const backtestForm = reactive({
  selection_strategy_id: '',
  selection_params: {}, // 后续可以用于存储和传递具体参数
  timing_strategy_id: '',
  timing_params: {},
  exit_strategy_id: '',
  exit_params: {},
  target_tickers_str: '', // 用户输入的逗号分隔的股票代码字符串
  backtest_config: {
    date_range: [new Date().getFullYear() - 3 + '-01-01', new Date().toISOString().split('T')[0]], // 默认最近三年
    initial_cash: 1000000,
    commission_bps: 2.5, // 万分之2.5
    benchmark_ticker: '000300.SH',
  }
});

const isBacktesting = ref(false);
const backtestResult = ref(null); // 存储回测结果
const showResultDetails = ref(false); // 控制是否展开详细结果
const activeCollapseNames = ref(['1']); // 默认展开哪个折叠面板

const equityCurveChartRef = ref(null);
let equityCurveChart = null;

onMounted(async () => {
  // 加载可选策略列表 (模拟)
  // availableSelectionStrategies.value = await fetchSelectionStrategies().data; // 假设API返回格式
  // availableTimingStrategies.value = await fetchTimingStrategies().data;
  // availableExitStrategies.value = await fetchExitStrategies().data;

  // 模拟数据填充
  availableSelectionStrategies.value = [{ id: 'value_momentum', name: '动量质量双引擎', params: {} }];
  availableTimingStrategies.value = [{ id: 'rsi_crossover', name: 'RSI超卖反弹', params: {} }];
  availableExitStrategies.value = [{ id: 'dynamic_sl_tp', name: '动态止盈止损', params: {} }];
});

const loadStrategyParams = (type) => {
    // TODO: 当选择策略后，可以加载该策略的默认参数或允许用户配置
    // 例如，弹出一个对话框让用户调整该策略的参数，然后存到 backtestForm[type + '_params']
    console.log(`Strategy selected for ${type}:`, backtestForm[`${type}_strategy_id`]);
};

const runBacktest = async () => {
  if (!backtestForm.selection_strategy_id || !backtestForm.timing_strategy_id || !backtestForm.exit_strategy_id) {
    ElMessage.warning('请选择完整的选品、择时和退出策略组合。');
    return;
  }
  if (!backtestForm.backtest_config.date_range || backtestForm.backtest_config.date_range.length !== 2) {
    ElMessage.warning('请选择有效的回测起止日期。');
    return;
  }

  isBacktesting.value = true;
  backtestResult.value = null; // 清空旧结果
  try {
    const payload = {
      selection_strategy: { id: backtestForm.selection_strategy_id, params: backtestForm.selection_params },
      timing_strategy: { id: backtestForm.timing_strategy_id, params: backtestForm.timing_params },
      exit_strategy: { id: backtestForm.exit_strategy_id, params: backtestForm.exit_params },
      backtest_config: {
        ...backtestForm.backtest_config,
        start_date: backtestForm.backtest_config.date_range[0],
        end_date: backtestForm.backtest_config.date_range[1],
      },
      target_tickers: backtestForm.target_tickers_str ? backtestForm.target_tickers_str.split(',').map(s => s.trim()).filter(s => s) : []
    };
    // const response = await apiRunBacktest(payload);
    // backtestResult.value = response.data;

    // 模拟API返回
    await new Promise(resolve => setTimeout(resolve, 2000));
    backtestResult.value = {
        performance_summary: {
            total_return: 0.887, annual_return: 0.187, max_drawdown: -0.224,
            sharpe_ratio: 1.32, sortino_ratio: 1.9, alpha: 0.06, beta: 0.85,
            win_rate: 0.628, profit_loss_ratio: 2.14
        },
        equity_curve: {
            strategy: Array.from({length:100}, (_,i) => ({date: `2022-${String(Math.floor(i/10)+1).padStart(2,'0')}-${String(i%10+1).padStart(2,'0')}`, value: 1000000 + i*i*100})),
            benchmark: Array.from({length:100}, (_,i) => ({date: `2022-${String(Math.floor(i/10)+1).padStart(2,'0')}-${String(i%10+1).padStart(2,'0')}`, value: 1000000 + i*5000}))
        },
        trades_summary: { total_trades: 126 },
        config_used: payload
    };


    ElMessage.success('回测完成！');
    nextTick(() => {
      renderEquityCurveChart();
    });
  } catch (error) {
    ElMessage.error(`回测失败: ${error.response?.data?.detail || error.message}`);
    console.error(error);
  } finally {
    isBacktesting.value = false;
  }
};

const renderEquityCurveChart = () => {
  if (!equityCurveChartRef.value || !backtestResult.value || !backtestResult.value.equity_curve) return;
  if (equityCurveChart) {
    equityCurveChart.dispose();
  }
  equityCurveChart = echarts.init(equityCurveChartRef.value);
  const option = {
    title: { text: '策略净值曲线' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['策略收益', '基准收益'] },
    grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: backtestResult.value.equity_curve.strategy.map(p => p.date) },
    yAxis: { type: 'value', scale: true, axisLabel: { formatter: '{value}' } },
    dataZoom: [{ type: 'inside', start: 0, end: 100 }, { start: 0, end: 10, handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z', handleSize: '80%', handleStyle: { color: '#fff', shadowBlur: 3, shadowColor: 'rgba(0, 0, 0, 0.6)', shadowOffsetX: 2, shadowOffsetY: 2 } }],
    series: [
      { name: '策略收益', type: 'line', smooth: true, showSymbol: false, data: backtestResult.value.equity_curve.strategy.map(p => p.value) },
      { name: '基准收益', type: 'line', smooth: true, showSymbol: false, data: backtestResult.value.equity_curve.benchmark.map(p => p.value) }
    ]
  };
  equityCurveChart.setOption(option);
};

const goBack = () => {
  router.back();
};

// 监听窗口大小变化以重绘图表
window.addEventListener('resize', () => {
  if (equityCurveChart) {
    equityCurveChart.resize();
  }
});

</script>

<style scoped>
.backtesting-lab-view {
  padding: 20px;
}
.el-page-header {
  margin-bottom: 20px;
}
.config-panel, .results-panel {
  height: 100%; /* 如果需要两侧等高 */
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.el-form-item {
    margin-bottom: 18px;
}
.el-tabs__content {
    padding-top: 15px;
}
pre {
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
}
</style>