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
                <el-button
                  type="primary"
                  @click="applyStrategyToHoldings"
                  :disabled="!selectedExitStrategyId || holdings.length === 0"
                  :loading="loadingSignals"
                >
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

          <el-table
            :data="holdingsWithDisplayDetails"
            stripe
            style="width: 100%"
            v-loading="loadingHoldings"
            empty-text="暂无持仓，请点击右上角添加"
          >
            <el-table-column prop="name" label="标的名称" width="150" />
            <el-table-column prop="ts_code" label="代码" width="100" />
            <el-table-column prop="cost_price" label="成本价" width="90">
                <template #default="scope">
                    {{ scope.row.cost_price !== null ? scope.row.cost_price.toFixed(2) : 'N/A' }}
                </template>
            </el-table-column>
            <el-table-column prop="current_price" label="当前价" width="90">
                <template #default="scope">
                    {{ scope.row.current_price !== null ? scope.row.current_price.toFixed(2) : 'N/A' }}
                </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column label="盈亏(%)" width="100">
              <template #default="scope">
                <span :class="getProfitLossClass(scope.row.profit_loss_percent)">
                  {{ scope.row.profit_loss_percent !== undefined && scope.row.profit_loss_percent !== null ? scope.row.profit_loss_percent.toFixed(2) + '%' : 'N/A' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="退出信号" width="200"> <!-- 宽度可能需要根据信号文本调整 -->
              <template #default="scope">
                <el-tag :type="getSignalTagType(scope.row.raw_signal)" v-if="scope.row.exit_signal_display" size="small">
                  {{ scope.row.exit_signal_display }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right"> <!-- 调整宽度以容纳按钮 -->
              <template #default="scope">
                <el-button size="small" type="danger" plain @click="removeHolding(scope.row.id)">移除</el-button>
                <!-- 编辑按钮可以后续添加 -->
                <!-- <el-button size="small" @click="editHolding(scope.row)">编辑</el-button> -->
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
        <!-- 股票名称由后端填充，前端不需输入
        <el-form-item label="股票名称" prop="name">
          <el-input v-model="addHoldingForm.name" placeholder="如 贵州茅台 (可选)" />
        </el-form-item>
        -->
        <el-form-item label="成本价格" prop="cost_price" :rules="[{ required: true, type: 'number', message: '请输入有效的成本价格', trigger: 'blur' }]">
          <el-input-number v-model="addHoldingForm.cost_price" :precision="2" :step="0.01" :min="0" style="width:100%;" />
        </el-form-item>
        <el-form-item label="持仓数量" prop="quantity" :rules="[{ required: true, type: 'integer', message: '请输入有效的持仓数量', trigger: 'blur' }]">
          <el-input-number v-model="addHoldingForm.quantity" :min="1" style="width:100%;" />
        </el-form-item>
        <el-form-item label="开仓日期" prop="open_date" :rules="[{ required: true, message: '请选择开仓日期', trigger: 'change' }]">
          <el-date-picker v-model="addHoldingForm.open_date" type="date" placeholder="选择日期" style="width:100%;" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input v-model="addHoldingForm.notes" type="textarea" placeholder="可选" />
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
import { // 导入新的API函数
  fetchExitStrategies,
  createHolding as apiCreateHolding,
  fetchHoldings as apiFetchHoldings,
  deleteHolding as apiDeleteHolding,
  checkExitSignalsForHoldings as apiCheckSignals
} from '@/api';
import { CirclePlus } from '@element-plus/icons-vue';

const router = useRouter();

const presetExitStrategies = ref([]);
const selectedExitStrategyId = ref('');
const selectedExitStrategy = computed(() => presetExitStrategies.value.find(s => s.id === selectedExitStrategyId.value));
const editableExitParams = reactive({});

const holdings = ref([]); // 将由API填充
const loadingHoldings = ref(false);
const loadingSignals = ref(false); // 用于检查信号时的加载状态

const showAddHoldingDialog = ref(false);
const addHoldingFormRef = ref(null);
const addHoldingForm = reactive({
  ts_code: '',
  // name: '', // 股票名称由后端根据ts_code填充，前端无需输入
  cost_price: null,
  quantity: null,
  open_date: new Date().toISOString().split('T')[0], // Pydantic模型需要date类型，但这里value-format="YYYY-MM-DD"会是字符串
  notes: ''
});

// 用于存储后端返回的退出信号，键为 holding.id
const exitSignalsMap = ref({});

// --- 数据获取函数 ---
const loadPresetExitStrategies = async () => {
  try {
    const response = await fetchExitStrategies();
    presetExitStrategies.value = response.data || []; // 确保是数组
    if (presetExitStrategies.value.length > 0) {
      // selectedExitStrategyId.value = presetExitStrategies.value[0].id; // 可以取消默认选中，让用户主动选择
      // handleStrategyChange(selectedExitStrategyId.value);
    }
  } catch (error) {
    ElMessage.error('获取退出策略列表失败');
    console.error("Error fetching exit strategies:", error);
  }
};

const loadHoldings = async () => {
  loadingHoldings.value = true;
  try {
    const response = await apiFetchHoldings(); // 假设不分页，或处理分页
    holdings.value = response.data || []; // 后端返回的数据应符合 HoldingItemResponse 结构
  } catch (error) {
    ElMessage.error('获取持仓列表失败');
    console.error("Error fetching holdings:", error);
    holdings.value = []; // 获取失败时清空
  } finally {
    loadingHoldings.value = false;
  }
};

onMounted(() => {
  loadPresetExitStrategies();
  loadHoldings();
});

// --- computed 属性，合并持仓和信号 ---
const holdingsWithDisplayDetails = computed(() => {
  return holdings.value.map(holding => {
    const signalInfo = exitSignalsMap.value[holding.id]; // 从map中获取对应信号
    let exit_signal_text = null;
    if (signalInfo) {
        // 可以根据 signalInfo.signal_type 和 signalInfo.notes 构造更详细的文本
        exit_signal_text = `${signalInfo.signal_type}: ${signalInfo.notes || `目标价 ${signalInfo.target_price}`}`;
    }

    return {
      ...holding, // holding中已经包含了current_price, profit_loss_percent等后端计算好的字段
      exit_signal_display: exit_signal_text, // 用于前端显示的信号文本
      raw_signal: signalInfo // 原始信号对象，可能用于其他判断
    };
  });
});

// --- 策略选择与参数处理 ---
const handleStrategyChange = (strategyId) => {
  const strategy = presetExitStrategies.value.find(s => s.id === strategyId);
  if (strategy && strategy.params) {
    // 清空之前的参数，防止不同策略的参数混淆
    for (const key in editableExitParams) {
        delete editableExitParams[key];
    }
    strategy.params.forEach(param => {
      editableExitParams[param.name] = param.value; // 使用策略定义的默认值
    });
  }
  // 清空已有的信号，因为策略变了
  exitSignalsMap.value = {};
};

// --- 持仓操作 ---
const resetAddHoldingForm = () => {
  if (addHoldingFormRef.value) {
    addHoldingFormRef.value.resetFields();
  }
  addHoldingForm.ts_code = '';
  addHoldingForm.cost_price = null;
  addHoldingForm.quantity = null;
  addHoldingForm.open_date = new Date().toISOString().split('T')[0];
  addHoldingForm.notes = '';
};

const confirmAddHolding = async () => {
  if (!addHoldingFormRef.value) return;
  await addHoldingFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 确保 open_date 是 'YYYY-MM-DD' 格式的字符串
        const dataToCreate = {
            ...addHoldingForm,
            open_date: addHoldingForm.open_date // el-date-picker value-format="YYYY-MM-DD" 保证了格式
        };
        await apiCreateHolding(dataToCreate);
        ElMessage.success('持仓添加成功');
        showAddHoldingDialog.value = false;
        await loadHoldings(); // 重新加载持仓列表
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '添加持仓失败');
        console.error("Error creating holding:", error);
      }
    } else {
      ElMessage.error('请检查表单输入');
      return false;
    }
  });
};

const removeHolding = async (holdingId) => { // 修改为接收 holdingId
  try {
    await ElMessageBox.confirm('确定要移除此持仓记录吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    await apiDeleteHolding(holdingId);
    ElMessage.success('持仓已移除');
    await loadHoldings(); // 重新加载持仓列表
    // 如果该持仓有信号，也从 exitSignalsMap 中移除
    if (exitSignalsMap.value[holdingId]) {
        delete exitSignalsMap.value[holdingId];
    }
  } catch (error) {
    if (error !== 'cancel') { // 用户点击取消时不提示错误
        ElMessage.error(error.response?.data?.detail || '移除持仓失败');
        console.error("Error deleting holding:", error);
    }
  }
};

// --- 信号检查 ---
const applyStrategyToHoldings = async () => {
  if (!selectedExitStrategy.value) {
    ElMessage.warning('请先选择一个退出策略并配置参数');
    return;
  }
  if (holdings.value.length === 0) {
    ElMessage.info('暂无持仓可应用策略');
    return;
  }

  loadingSignals.value = true;
  exitSignalsMap.value = {}; // 清空旧信号

  try {
    const requestData = {
      // holding_ids: holdings.value.map(h => h.id), // 可以选择发送所有持仓ID
      holding_ids: null, // 或者发送null，让后端检查所有
      strategy_id: selectedExitStrategy.value.id,
      params: { ...editableExitParams },
    };
    const response = await apiCheckSignals(requestData);
    if (response.data && response.data.signals) {
      const newSignalsMap = {};
      response.data.signals.forEach(signal => {
        newSignalsMap[signal.holding_id] = signal;
      });
      exitSignalsMap.value = newSignalsMap; // 更新信号 Map
      if (response.data.signals.length > 0) {
        ElMessage.success('退出信号已检查完毕');
      } else {
        ElMessage.info('所有持仓均未触发退出信号');
      }
    } else {
      ElMessage.info('所有持仓均未触发退出信号');
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '检查退出信号失败');
    console.error("Error checking exit signals:", error);
  } finally {
    loadingSignals.value = false;
  }
};

// --- 辅助函数与样式 ---
const getProfitLossClass = (percent) => {
  if (percent === undefined || percent === null) return '';
  return percent >= 0 ? 'positive-text' : 'negative-text';
};

const getSignalTagType = (signalInfo) => { // signalInfo 是 ExitSignalItem 对象
  if (!signalInfo || !signalInfo.signal_type) return 'info';
  if (signalInfo.signal_type.includes('STOP_LOSS')) return 'danger';
  if (signalInfo.signal_type.includes('TAKE_PROFIT')) return 'success';
  return 'primary';
};

const goBack = () => {
  router.back();
};

// 当前价格输入框的逻辑 (暂时移除，因为当前价格由后端获取)
// const recalculateSignal = (holdingRow) => {};
// watch(editableExitParams, recalculateAllSignals, { deep: true }); // 暂时移除本地计算
// const recalculateAllSignals = () => {}; // 暂时移除本地计算
</script>

<style scoped>
/* 样式与您提供的保持一致 */
.exit-engine-view {
  padding: 20px;
}
.el-page-header {
  margin-bottom: 20px;
}
.control-panel, .holdings-panel {
  height: 100%;
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
// --- END OF FILE frontend/src/views/exit/ExitEngineView.vue ---