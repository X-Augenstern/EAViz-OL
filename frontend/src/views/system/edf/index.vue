<template>
  <div class="app-container">
    <!-- EDF查询表单 -->
    <!-- 
    @keyup.enter 这个事件是 Vue.js 框架自带的事件修饰符，用来监听特定的键盘事件。
    @keyup 是 Vue.js 中用于监听键盘按键抬起事件的指令。 
    .enter 是一个事件修饰符，表示仅当按下的是 Enter 键时才触发事件。
    表示在用户按下 Enter 键并抬起时，调用 handleQuery 方法。这是 Vue.js 提供的便捷语法，用于简化键盘事件的监听和处理。
    -->
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="EDF名称" prop="edfName">
        <el-input v-model="queryParams.edfName" placeholder="请输入EDF名称" clearable style="width: 240px"
          @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="上传用户" prop="uploadBy" v-if="userStore.id === 1">
        <el-input v-model="queryParams.uploadBy" placeholder="请输入上传用户名称" clearable style="width: 240px"
          @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="上传时间" style="width: 308px;">
        <el-date-picker v-model="dateRange" value-format="YYYY-MM-DD" type="daterange" range-separator="-"
          start-placeholder="开始日期" end-placeholder="结束日期"></el-date-picker>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="info" plain icon="Upload" @click="handleImport"
          v-hasPermi="['system:edf:import']">导入</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="!hasSelect" @click="handleDelete"
          v-hasPermi="['system:edf:remove']">删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList" :columns="columns"></right-toolbar>
    </el-row>

    <!-- EDF表格 -->
    <el-table v-loading="loading" :data="edfList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="50" align="center" />
      <el-table-column label="EDF编号" align="center" key="edfId" prop="edfId" v-if="columns[0].visible" />
      <el-table-column label="EDF名称" align="center" key="edfName" prop="edfName" v-if="columns[1].visible"
        :show-overflow-tooltip="true" />
      <el-table-column label="上传用户" align="center" key="uploadBy" prop="uploadBy" v-if="columns[2].visible"
        :show-overflow-tooltip="true" />
      <el-table-column label="上传时间" align="center" key="uploadTime" prop="uploadTime" v-if="columns[3].visible"
        :show-overflow-tooltip="true">
        <!-- 
        scope 是一个对象，包含当前单元格和行的数据。具体来说：
            row: 当前行的数据对象。
                row: Proxy(Object) {edfId: 6, edfName: 'liang_19_labeled_filtered_reduced.edf', edfPath: 'files/upload_path\\upload/2024/07/08\\liang_19_labeled_filtered_reduced_20240708104117A344.edf', uploa
            column: 当前列的数据对象。
                column: {order: '', id: 'el-table_2_column_11', type: 'default', property: 'uploadTime', align: 'is-center', …}
            index: 当前行的索引（从0开始）。
                $index: 0
            store: 表格的数据存储对象，通常用来管理表格状态。
                store: {ns: {…}, assertRowKey: ƒ, updateColumns: ƒ, scheduleLayout: ƒ, isSelected: ƒ, …}
        -->
        <template #default="scope">
          <span>{{ parseTime(scope.row.uploadTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="150" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-tooltip content="删除" placement="top" v-if="scope.row.userId !== 1">
            <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)"
              v-hasPermi="['system:edf:remove']"></el-button>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>
    <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize" @pagination="getList" />

    <!-- EDF导入对话框 -->
    <el-dialog :title="uploadParam.title" v-model="uploadParam.open" width="400px" append-to-body>
      <el-upload ref="uploadRef" accept=".edf" :headers="uploadParam.headers" :action="uploadParam.url"
        :disabled="uploadParam.isUploading" :on-change="handleFileChange" :on-progress="handleFileUploadProgress"
        :on-success="handleFileSuccess" :on-error="handleFileError" :auto-upload="false" drag multiple name="files">
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip text-center">
            <span>仅允许导入edf格式文件。</span>
          </div>
        </template>
      </el-upload>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitFileForm">确 定</el-button>
          <el-button @click="clearFileList">清 空</el-button>
          <el-button @click="uploadParam.open = false">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="EDF">
import { getToken } from "@/utils/auth";
import { listEdf, delEdf } from "@/api/system/edf";
import { onMounted, ref, toRef, toRefs } from "vue";
import useUserStore from "@/store/modules/user";

const { proxy } = getCurrentInstance();
const edfList = ref([]);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const hasSelect = ref(false);
const total = ref(0);
const dateRange = ref([]);
const userStore = useUserStore();

/** EDF导入参数 */
const uploadParam = reactive({
  // 是否显示弹出层（EDF导入）
  open: false,
  // 弹出层标题（EDF导入）
  title: "",
  // 是否禁用上传
  isUploading: false,
  // 设置上传的请求头部
  headers: { Authorization: "Bearer " + getToken() },
  // 上传的地址
  url: import.meta.env.VITE_APP_BASE_API + "/system/edf/importData",  // '/dev-api/system/edf/importData',
  // 上传文件数量
  totalFiles: 0,
  // 上传成功文件数量
  uploadedFiles: 0,
  // 上传响应信息
  responses: []
});

/** 列显隐信息 */
const columns = ref([
  { key: 0, label: `EDF编号`, visible: true },
  { key: 1, label: `EDF名称`, visible: true },
  { key: 2, label: `上传者`, visible: true },
  { key: 3, label: `上传时间`, visible: true },
]);

/** 查询参数 */
const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    edfName: undefined,
    uploadBy: undefined,
    uploadTime: undefined,
  },
  // rules: {
  //   edfName: [{ required: true, message: "用户名称不能为空", trigger: "blur" }, { min: 2, max: 20, message: "用户名称长度必须介于 2 和 20 之间", trigger: "blur" }],
  //   updateBy: [{ required: true, message: "用户昵称不能为空", trigger: "blur" }],
  //   updateTime: [{ required: true, message: "用户密码不能为空", trigger: "blur" }, { min: 5, max: 20, message: "用户密码长度必须介于 5 和 20 之间", trigger: "blur" }],
  //   email: [{ type: "email", message: "请输入正确的邮箱地址", trigger: ["blur", "change"] }],
  //   phonenumber: [{ pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: "请输入正确的手机号码", trigger: "blur" }]
  // }
});

// 使用 toRefs 将 reactive 对象的属性转换为独立的 ref 对象后，它们仍然保持响应性。
// 这意味着，如果改变了 data 中的属性值，这些独立的 ref 对象也会相应变化；反之亦然，如果改变了这些 ref 对象的值，data 中的属性值也会相应变化。
// toRef 用于将 reactive 对象中的单个属性转换为一个 ref 对象。这样可以使得该属性保持响应性，同时可以独立使用。
// toRefs 用于将 reactive 对象中的所有属性转换为对应的 ref 对象。这样可以使得所有属性保持响应性，同时可以独立使用。这在需要解构响应式对象并保持响应性时特别有用。
// 或 const { queryParams, form, rules } = toRefs(data);
// 或 const { queryParams } = toRefs(data);
const queryParams = toRef(data, 'queryParams');

onMounted(() => {
  getList();
})

/** 查询Edf列表 */
function getList() {
  loading.value = true;
  listEdf(proxy.addDateRange(queryParams.value, dateRange.value)).then(res => {
    loading.value = false;
    edfList.value = res.rows;
    total.value = res.total;
  });
};

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
};

/** 重置按钮操作 */
function resetQuery() {
  dateRange.value = [];
  proxy.resetForm("queryRef");
  handleQuery();
};

/** 删除按钮操作 */
function handleDelete(row) {
  const edfIds = row.edfId || ids.value;
  proxy.$modal.confirm('是否确认删除EDF编号为"' + edfIds + '"的数据项？').then(function () {
    return delEdf(edfIds);
  }).then(() => {
    getList();
    proxy.$modal.msgSuccess("删除成功");
  }).catch(() => { });
};

/** 选择项发生变化  */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.edfId);
  hasSelect.value = selection.length !== 0;
};

/** 导入按钮操作 */
function handleImport() {
  uploadParam.title = "EDF导入";
  uploadParam.open = true;
};

/** 
 * 文件改变处理
 * 
 * 添加文件、上传成功和上传失败时都会被调用
 * 
 * 所以上传成功时如果调用 proxy.$refs["uploadRef"].handleRemove(file); -> fileList.length -1
 */
const handleFileChange = (file, fileList) => {
  uploadParam.totalFiles = fileList.length;
  // Proxy(Array) {0: Proxy(Object), 1: Proxy(Object), 2: Proxy(Object), 3: {…}}
  // console.log(fileList)

  // {name: 'liang_19_labeled_filtered_reduced.edf', percentage: 0, status: 'ready', size: 11621376, raw: File, …}
  // console.log(file)
}

/** 提交上传文件（一批只会执行一次） */
function submitFileForm() {
  if (uploadParam.totalFiles === 0) {
    proxy.$alert(
      "<div style='overflow: auto;overflow-x: hidden;max-height: 70vh;padding: 10px 20px 0;'>"
      + "未选择任何EDF文件" +
      "</div>", "警告", { dangerouslyUseHTMLString: true });
    return;
  }

  // 重置
  uploadParam.uploadedFiles = 0;
  uploadParam.responses = [];

  proxy.$refs["uploadRef"].submit();
};

/** 文件上传中处理 */
const handleFileUploadProgress = (event, file, fileList) => {
  uploadParam.isUploading = true;
};

/** 文件上传成功处理（每上传成功一个就执行一次） */
const handleFileSuccess = (response, file, fileList) => {
  uploadParam.uploadedFiles++;
  uploadParam.responses.push(response.msg)

  if (uploadParam.uploadedFiles === uploadParam.totalFiles) {
    uploadParam.open = false;
    uploadParam.isUploading = false;
    const allResonses = uploadParam.responses.join('<br>')  // 定义简单的折行

    proxy.$alert(
      "<div style='overflow: auto;overflow-x: hidden;max-height: 70vh;padding: 10px 20px 0;'>"
      + allResonses +
      "</div>", "导入结果", { dangerouslyUseHTMLString: true });

    getList();

    // 重置
    uploadParam.uploadedFiles = 0;
    uploadParam.responses = [];
    clearFileList();
  }
};

/** 文件上传失败处理（每上传失败一个就执行一次） */
const handleFileError = (err, file, fileList) => {
  uploadParam.uploadedFiles++;
  uploadParam.responses.push(`${file.name}上传失败：${response.msg} 错误信息：${err}`)

  if (uploadParam.uploadedFiles === uploadParam.totalFiles) {
    uploadParam.open = false;
    uploadParam.isUploading = false;
    const allResonses = uploadParam.responses.join('<br>')  // 定义简单的折行

    proxy.$alert(
      "<div style='overflow: auto;overflow-x: hidden;max-height: 70vh;padding: 10px 20px 0;'>"
      + allResonses +
      "</div>", "导入结果", { dangerouslyUseHTMLString: true });

    getList();

    // 重置
    uploadParam.uploadedFiles = 0;
    uploadParam.responses = [];
    clearFileList();
  }
}

/** 清空文件列表 */
const clearFileList = () => {
  proxy.$refs["uploadRef"].clearFiles();
  uploadParam.totalFiles = 0;
}
</script>
