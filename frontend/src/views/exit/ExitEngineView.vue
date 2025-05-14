// frontend/src/views/exit/ExitEngineView.vue
<template>
  <div class="exit-engine-view">
    <el-page-header title="幻方黑匣 · 退出引擎" content="智能管理持仓，锁定盈利，控制风险" @back="goBack" />
    <el-divider />

    <el-row :gutter="20">
      <!-- 左侧：策略选择与参数调整 -->
      <el-col :xs="24" :md="8">
        <el-card shadow="never" class="control-panel">
          <template #header>
            <div class="card-header">
              <span>退出策略配置</span>
            </div>
          </template>

          <el-form label-width="100px" label-position="top">
            <el-form-item label="选择退出策略">
              <el-select v-model="selectedExitStrategyId" placeholder="请选择策略" style="width: 100%;" @change="handleStrategyChange">
                <el-option
                  v-for="strategy in presetExitStrategies"
                  :key="strategy.id"
                  :label="strategy.name"
                  :value="strategy.id"
                />
              </el-select>
            </el-form-item>

            <div v-if="selectedExitStrategy" class="strategy-params">
              <p style="margin-bottom: 10px; font-size: 14px; color: #606266;">{{ selectedExitStrategy.description }}</p>
              <el-form-item
                v-for="param in selectedExitStrategy.params"
                :key="param.name"
                :label="param.description || param.name"
              >
                <el-slider
                  v-model="editableExitParams[param.name]"
                  :min="param.min_value"
                  :max="param.max_value"
                  :step="param.step"
                  show-input
                />
                <span style="margin-left: 10px; font-size:12px; color: #909399;">{{ param.unit || '' }}</span>
              </el-form-item>
            </div>
            <el-form-item>
                <el-button type="primary" @click="applyStrategyToHoldings" :disabled="!selectedExitStrategyId || holdings.length === 0">
                    应用策略到所有持仓
                </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：持仓列表与退出信号 -->
      <el-col :xs="24" :md="16">
        <el-card shadow="never" class="holdings-panel">
          <template #header>
            <div class="card-header">
              <span>我的持仓</span>
              <el-button type="success" :icon="CirclePlus" @click="showAddHoldingDialog = true">添加持仓</el-button>
            </div>
          </template>

          <el-table :data="holdingsWithSignals" stripe style="width: 100%" v-loading="loadingHoldings" empty-text="暂无持仓，请点击右上角添加">
            <el-table-column prop="name" label="标的名称" width="150" />
            <el-table-column prop="ts_code" label="代码" width="100" />
            <el-table-column prop="cost_price" label="成本价" width="90" />
            <el-table-column prop="current_price" label="当前价" width="90">
                <template #default="scope">
                    <el-input v-model.number="scope.row.current_price" size="small" @change="recalculateSignal(scope.row)" placeholder="输入模拟" />
                </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column label="盈亏(%)" width="100">
              <template #default="scope">
                <span :class="getProfitLossClass(scope.row.profit_loss_percent)">
                  {{ scope.row.profit_loss_percent !== undefined ? scope.row.profit_loss_percent.toFixed(2) + '%' : 'N/A' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="exit_signal" label="退出信号" width="150">
              <template #default="scope">
                <el-tag :type="getSignalTagType(scope.row.exit_signal)" v-if="scope.row.exit_signal" size="small">
                  {{ scope.row.exit_signal }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button size="small" type="danger" plain @click="removeHolding(scope.$index)">移除</el-button>
                <!-- <el-button size="small" @click="viewHoldingHistory(scope.row)">历史</el-button> -->
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加持仓对话框 -->
    <el-dialog v-model="showAddHoldingDialog" title="添加新的持仓" width="500px" @close="resetAddHoldingForm">
      <el-form :model="addHoldingForm" ref="addHoldingFormRef" label-width="100px">
        <el-form-item label="股票代码" prop="ts_code" :rules="[{ required: true, message: '请输入股票代码', trigger: 'blur' }]">
          <el-input v-model="addHoldingForm.ts_code" placeholder="如 600519.SH" />
        </el-form-item>
        <el-form-item label="股票名称" prop="name">
          <el-input v-model="addHoldingForm.name" placeholder="如 贵州茅台 (可选)" />
        </el-form-item>
        <el-form-item label="成本价格" prop="cost_price" :rules="[{ required: true, type: 'number', message: '请输入有效的成本价格', trigger: 'blur' }]">
          <el-input-number v-model="addHoldingForm.cost_price" :precision="2" :step="0.01" :min="0" style="width:100%;" />
        </el-form-item>
        <el-form-item label="持仓数量" prop="quantity" :rules="[{ required: true, type: 'integer', message: '请输入有效的持仓数量', trigger: 'blur' }]">
          <el-input-number v-model="addHoldingForm.quantity" :min="1" style="width:100%;" />
        </el-form-item>
        <el-form-item label="买入日期" prop="buy_date">
          <el-date-picker v-model="addHoldingForm.buy_date" type="date" placeholder="选择日期" style="width:100%;" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddHoldingDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmAddHolding">确定添加</el-button>
        </span>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { fetchExitStrategies, checkExitSignalsForHoldings as apiCheckSignals } from '@/api'; // 假设 API 服务已封装
import { CirclePlus } from '@element-plus/icons-vue';

const router = useRouter();

const presetExitStrategies = ref([]);
const selectedExitStrategyId = ref('');
const selectedExitStrategy = computed(() => presetExitStrategies.value.find(s => s.id === selectedExitStrategyId.value));
const editableExitParams = reactive({});

const holdings = ref([ // 用户持仓列表，后续应通过API或Pinia管理
  // 示例数据
  { id: 1, ts_code: '600519.SH', name: '贵州茅台', cost_price: 1600.00, quantity: 100, buy_date: '2023-01-15', current_price: 1780.50 },
  { id: 2, ts_code: '000001.SZ', name: '平安银行', cost_price: 11.50, quantity: 1000, buy_date: '2023-03-10', current_price: 10.50 },
]);
const loadingHoldings = ref(false);

const showAddHoldingDialog = ref(false);
const addHoldingFormRef = ref(null);
const addHoldingForm = reactive({
  ts_code: '',
  name: '',
  cost_price: null,
  quantity: null,
  buy_date: new Date().toISOString().split('T')[0] // 默认今天
});

// 计算每个持仓的盈亏和退出信号
const holdingsWithSignals = computed(() => {
  return holdings.value.map(holding => {
    let profit_loss_percent;
    if (holding.current_price && holding.cost_price) {
      profit_loss_percent = ((holding.current_price - holding.cost_price) / holding.cost_price) * 100;
    } else {
      profit_loss_percent = undefined;
    }

    // 根据选定策略和参数计算退出信号 (简化版，实际应更复杂)
    let exit_signal = null;
    if (selectedExitStrategy.value && holding.current_price) {
        const params = editableExitParams;
        if (selectedExitStrategy.value.id === 'dynamic_stop_profit_loss') { // 假设策略ID
            const stopLossPercent = params.stop_loss_percent / 100;
            const takeProfitPercent = params.take_profit_percent / 100;

            if (profit_loss_percent <= -stopLossPercent * 100) {
                exit_signal = `触发止损 (${params.stop_loss_percent}%)`;
            } else if (profit_loss_percent >= takeProfitPercent * 100) {
                exit_signal = `达到止盈 (${params.take_profit_percent}%)`;
            }
            // 还可以添加移动止盈等逻辑
        }
        // ... 其他策略的判断 ...
    }

    return {
      ...holding,
      profit_loss_percent,
      exit_signal
    };
  });
});


onMounted(async () => {
  try {
    // const response = await fetchExitStrategies();
    // presetExitStrategies.value = response.data;
    presetExitStrategies.value = [ // 模拟数据
        { id: 'dynamic_stop_profit_loss', name: '动态止盈止损', description: '设置固定的止盈和止损百分比。', params: [{name: 'take_profit_percent', value: 20, min_value:5, max_value:100, unit:'%'}, {name: 'stop_loss_percent', value: 10, min_value:1, max_value:50, unit:'%'}]},
        { id: 'atr_trailing_stop', name: 'ATR追踪止损', description: '使用ATR指标动态调整止损位。', params: [{name: 'atr_period', value: 14, min_value:5, max_value:30, unit:'周期'}, {name: 'atr_multiplier', value: 3, min_value:1, max_value:5, unit:'倍数'}]},
    ];
    if (presetExitStrategies.value.length > 0) {
        // selectedExitStrategyId.value = presetExitStrategies.value[0].id; // 默认选中第一个
        // handleStrategyChange(selectedExitStrategyId.value); // 初始化参数
    }
  } catch (error) {
    ElMessage.error('获取退出策略列表失败');
    console.error(error);
  }
});

const handleStrategyChange = (strategyId) => {
  const strategy = presetExitStrategies.value.find(s => s.id === strategyId);
  if (strategy && strategy.params) {
    strategy.params.forEach(param => {
      editableExitParams[param.name] = param.value;
    });
  }
  // 触发一次信号重新计算
  recalculateAllSignals();
};

const applyStrategyToHoldings = async () => {
  if (!selectedExitStrategy.value) {
    ElMessage.warning('请先选择一个退出策略并配置参数');
    return;
  }
  ElMessage.success(`"${selectedExitStrategy.value.name}" 策略已应用到所有持仓的信号计算中。`);
  recalculateAllSignals(); // 本地模拟，实际可能需要调用API

  // 如果需要后端进行信号计算：
  // loadingHoldings.value = true;
  // try {
  //   const holdingsData = holdings.value.map(h => ({ ts_code: h.ts_code, cost_price: h.cost_price, quantity: h.quantity, current_price: h.current_price }));
  //   const requestData = {
  //     strategy_id: selectedExitStrategy.value.id,
  //     params: { ...editableExitParams },
  //     holdings: holdingsData
  //   };
  //   const response = await apiCheckSignals(requestData);
  //   // 更新 holdings.value 中的 exit_signal 字段
  //   response.data.signals.forEach(signalInfo => {
  //       const holdingToUpdate = holdings.value.find(h => h.ts_code === signalInfo.ts_code);
  //       if (holdingToUpdate) {
  //           holdingToUpdate.exit_signal = signalInfo.signal;
  //       }
  //   });
  //   ElMessage.success('退出信号已从服务器更新');
  // } catch (error) {
  //   ElMessage.error('更新退出信号失败');
  // } finally {
  //   loadingHoldings.value = false;
  // }
};

const recalculateSignal = (holdingRow) => {
    // 当current_price手动修改时，强制重新计算该行的信号
    // 这是一个hacky的方式，更好的方式是让holdingsWithSignals能够响应editableExitParams的变化
    // 这里通过修改一个无关紧要的属性来触发computed属性的重新计算
    holdingRow.id = holdingRow.id; // 或者使用更Vue的方式，例如深度watch editableExitParams
};

const recalculateAllSignals = () => {
    // 强制重新计算所有信号
    holdings.value = [...holdings.value];
}

watch(editableExitParams, () => {
    // 当策略参数变化时，自动重新计算所有信号
    recalculateAllSignals();
}, { deep: true });


const resetAddHoldingForm = () => {
  if (addHoldingFormRef.value) {
    addHoldingFormRef.value.resetFields();
  }
  addHoldingForm.ts_code = '';
  addHoldingForm.name = '';
  addHoldingForm.cost_price = null;
  addHoldingForm.quantity = null;
  addHoldingForm.buy_date = new Date().toISOString().split('T')[0];
};

const confirmAddHolding = async () => {
  if (!addHoldingFormRef.value) return;
  await addHoldingFormRef.value.validate((valid) => {
    if (valid) {
      holdings.value.push({
        id: Date.now(), // 简单唯一ID
        ...addHoldingForm,
        current_price: addHoldingForm.cost_price // 初始当前价等于成本价
      });
      ElMessage.success('持仓添加成功');
      showAddHoldingDialog.value = false;
      recalculateAllSignals();
    } else {
      ElMessage.error('请检查表单输入');
      return false;
    }
  });
};

const removeHolding = (index) => {
  ElMessageBox.confirm('确定要移除此持仓记录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    holdings.value.splice(index, 1);
    ElMessage.success('持仓已移除');
    recalculateAllSignals();
  }).catch(() => {
    // ElMessage.info('已取消移除');
  });
};

const getProfitLossClass = (percent) => {
  if (percent === undefined || percent === null) return '';
  return percent >= 0 ? 'positive-text' : 'negative-text';
};

const getSignalTagType = (signal) => {
  if (!signal) return 'info';
  if (signal.includes('止损') || signal.includes('卖出')) return 'danger';
  if (signal.includes('止盈')) return 'success';
  return 'primary';
};

const goBack = () => {
  router.back();
};
</script>

<style scoped>
.exit-engine-view {
  padding: 20px;
}
.el-page-header {
  margin-bottom: 20px;
}
.control-panel, .holdings-panel {
  height: 100%; /* 如果需要两侧等高 */
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.strategy-params {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #ebeef5;
}
.positive-text {
  color: #67c23a;
}
.negative-text {
  color: #f56c6c;
}
</style>