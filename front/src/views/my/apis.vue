<template>
  <div class="app-container">
    <el-form
      ref="regeditForm"
      :model="regeditForm"
      :inline="false"
    >
      <el-form-item>
        <el-upload
          ref="upload"
          class="upload-demo"
          action="https://jsonplaceholder.typicode.com/posts/"
          :http-request="httpRequest"
          :auto-upload="false"
          :on-preview="handlePreview"
          :on-remove="handleRemove"
          :before-remove="beforeRemove"
          multiple
          :limit="3"
          :on-exceed="handleExceed"
          :file-list="fileList"
        >
          <el-button size="small" type="primary">上传测试用例配置</el-button>
          <div slot="tip" class="el-upload__tip">只能上传.py .json文件，且不超过500kb</div>
        </el-upload>
        <el-button size="small" type="primary" @click="register('regeditForm')">提交</el-button>
      </el-form-item>
    </el-form>
    <div class="refresh">
      <el-button class="el-icon-refresh-right" @click="refresh"/>
    </div>

  </div>
</template>

<script>
export default {
  inject: ['reload'],
  data() {
    return {}
  },
  created() {
    this.getClassConfig()
  },
  methods: {
    refresh() {
      this.reload()
    }
  }
}
</script>

