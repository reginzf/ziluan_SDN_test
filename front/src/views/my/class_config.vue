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
      <el-table
        :data="tableData"
        style="width: 100%"
      >
        <el-table-column
          prop="name"
          label="配置文件名称"
          width="180"
        />
        <el-table-column
          prop="testcase_name"
          label="测试点名称"
          width="180"
        />
        <el-table-column
          prop="size"
          label="大小"
          width="180"
        />
        <el-table-column
          prop="last_modify"
          label="更新时间"
          width="180"
        />
        <el-table-column
          prop="description"
          label="描述"
          width="240"
        />
        <el-table-column label="操作" min-width="100" align="center">
          <template v-slot="scope">
            <el-button type="danger" size="small" @click="deleteClass(scope.row.name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

  </div>
</template>

<script>
export default {
  inject: ['reload'],
  data() {
    return {
      fileList: [],
      regeditForm: {
        name: '名称',
        description: '描述',
        url: '/upload_config'
      },
      tableData: null
    }
  },
  created() {
    this.getClassConfig()
  },
  methods: {
    deleteClass(name) {
      const url = '/delete_file_config'
      this.axios.post(url, {
        'file': name
      }).then(res => {
        if (res.data.code === 'success') {
          this.$message({
            message: '删除测试用例配置' + name + '成功',
            type: 'success'
          })
        } else {
          this.$message({
            message: '删除测试用例配置' + name + '失败'
          })
        }
      })
    },
    refresh() {
      this.reload()
    },
    getClassConfig() {
      this.axios.get('/show_class_config')
        .then(res => {
          this.tableData = res.data.msg
        }).catch(error => {
        console.log(error)
      })
    },
    httpRequest(param) {
      const fileObj = param.file
      const data = new FormData()
      data.append('file', fileObj)
      data.append('name', this.regeditForm.name)
      data.append('description', this.regeditForm.description)
      this.axios({
        method: 'post',
        url: '/upload_config',
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        data: data
      }).then(res => {
        console.log(res)
      }).catch(error => {
        console.log(error)
      })
    },
    register(fileName) {
      // todo 检查文件名
      this.$refs.upload.submit()
    },
    handleRemove(file, fileList) {
      console.log(file, fileList)
    },
    handlePreview(file) {
      console.log(file)
    },
    handleExceed(files, fileList) {
      this.$message.warning(`当前限制选择 2 个文件，本次选择了 ${files.length} 个文件，共选择了 ${files.length + fileList.length} 个文件`)
    },
    beforeRemove(file, fileList) {
      return this.$confirm(`确定移除 ${file.name}？`)
    }
  }
}
</script>

