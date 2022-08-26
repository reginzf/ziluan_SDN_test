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
          <el-button size="small" type="primary">上传测试用例</el-button>
          <div slot="tip" class="el-upload__tip">只能上传.py .json文件，且不超过500kb</div>
        </el-upload>
      </el-form-item>
      <el-form-item style="text-align: left;width: 430px">
        <el-button type="primary" @click="register('regeditForm')">提交</el-button>
      </el-form-item>
    </el-form>

    <div class="refresh">
    <div>
      <el-input  placeholder="请输入关键字"  v-model="search" style="width:240px" type ="primary"></el-input>
	  <el-button type="primary" @click="doFilter">搜索</el-button>
      <el-button class="el-icon-refresh-right" @click="refresh" />

      </div>
      <el-table
        :data="pageInfo"
        style="width: 100%"
      >
        <el-table-column
          prop="name"
          label="测试用例名称"
          width="180"
        />
        <el-table-column
          prop="size"
          label="大小"
          width="100"
        />
        <el-table-column
          prop="last_modify"
          label="更新时间"
          width="180"
        />
        <el-table-column prop="status" label="状态" width="100">
          <template v-slot="scope">
            <span v-if="scope.row.status==='已加载'" style="color: green">{{ scope.row.status }}</span>
            <span v-else style="color: red">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          label="描述"
          width="240"
        />
        <el-table-column label="操作" min-width="100" align="center">
          <template v-slot="scope">
            <el-button type="success" size="small" @click="startTask(scope.row.name)">启动</el-button>
            <el-button type="primary" size="small" @click="loadClass(scope.row.name)">加载</el-button>
            <el-button type="warning" size="small" @click="unloadClass(scope.row.name)">卸载</el-button>
            <el-button type="danger" size="small" @click="deleteClass(scope.row.name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        :current-page="currentPage"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total_size"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
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
        url: 'http://172.25.0.86:10001/upload'
      },
      tableData: null,
	    pageInfo:null,
      total_size: null,
      currentPage: 1,
      pageSize: 10,
      search: '',
	  searchInfo: null
    }
  },
  created() {
    this.getClass()
  },
  methods: {
    deleteClass(name) {
      const url = '/delete_file'
      this.axios.post(url, {
        'file': name
      }).then(res => {
        if (res.data.code === 'success') {
          this.$message({
            message: '删除测试用例：' + name + '成功',
            type: 'success'
          })
          this.refresh()
        } else {
          this.$message({
            message: '删除测试用例：' + name + '失败' + res.data.error_msg,
            type: 'error'
          })
        }
      })
    },
    startTask(name) {
      name = name.split('.py')[0]
      const url = '/run_new_taskset/' + name
      this.axios.get(url).then(res => {
        if (res.data.code === 'success') {
          this.$message({
            message: '任务' + name + '启动成功\n' + res.data.msg,
            type: 'success'
          })
        } else {
          this.$message({
            message: '任务' + name + '启动失败\n' + res.data.msg,
            type: 'error'
          })
        }
      })
    },
    unloadClass(name) {
      name = name.split('.py')[0]
      const url = '/remove_taskcase_class/' + name + '/' + name
      this.axios.get(url).then(res => {
        if (res.data.code === 'success') {
          this.$message({
            message: '卸载测试用例' + name + '成功',
            type: 'success'
          })
          this.refresh()
        } else {
          this.$message({
            message: '卸载测试用例' + name + '失败',
            type: 'error'
          })
        }
      })
    },
    loadClass(name) {
      name = name.split('.py')[0]
      // let name_ = name.split('.py')[0]
      var url = '/registe_testcast_class/' + name + '/' + name
      this.axios.get(url).then(res => {
        if (res.data.code === 'success') {
          this.$message({
            message: '加载测试用例' + name + '成功',
            type: 'success'
          })
          this.refresh()
        } else {
          this.$message({
            message: '加载测试用例' + name + '失败',
            type: 'error'
          })
        }
      }
      )
    },
    refresh() {
      this.reload()
    },
    getClass() {
      this.axios.get('/show_class')
        .then(res => {
          this.tableData = res.data.msg
          this.total_size = this.tableData.length
          this.getPageInfo()
        }).catch(error => {
          console.log(error)
        })
    },
  getPageInfo(){
		var start = (this.currentPage - 1) * this.pageSize
		var end = start + this.pageSize
		var searchInfo = this.searchInfo
		if(searchInfo){
		  if(end > searchInfo.length ){
			  end = searchInfo.length
		  }
		  this.pageInfo = searchInfo.slice(start,end)
	    } else {
			if( end > this.total_size) {
				end = this.total_size
			}
			this.pageInfo = this.tableData.slice(start,end)
		  }
		},
  doFilter(){
	  var search = this.search
	  var pageInfo=[]
	  if(search){
		  this.currentPage = 1
		  this.tableData.forEach(function(value,index,array){
			  if(value['name'].includes(search)){
				  pageInfo.push(value)
			  }
		  })
	  }
	  this.searchInfo = pageInfo
	  this.total_size = pageInfo.length
	  this.getPageInfo()

  },
	handleSizeChange(size){
		this.pageSize = size
		this.getPageInfo()
	},
	handleCurrentChange(pageNumber){
		this.currentPage=pageNumber
		this.getPageInfo()
	},
    httpRequest(param) {
      const fileObj = param.file
      const data = new FormData()
      data.append('file', fileObj)
      data.append('name', this.regeditForm.name)
      data.append('description', this.regeditForm.description)
      this.axios({
        method: 'post',
        url: 'upload',
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

