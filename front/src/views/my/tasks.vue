<template>
  <div class="app-container">
    <div class="refresh">
      <el-button class="el-icon-refresh-right" @click="refresh" />
      <el-table
        :data="tableData"
        style="width: 100%"
      >
        <el-table-column
          prop="name"
          label="任务名称"
          width="180"
        />
        <el-table-column
          prop="interval"
          label="执行间隔"
          width="100"
        />
        <el-table-column
          prop="rantimes"
          label="已执行次数"
          width="100"
        />
        <el-table-column
          prop="runtimes"
          label="设定执行次数"
          width="120"
        />
        <el-table-column
          prop="starttime"
          label="开始时间"
          width="120"
        />
        <el-table-column
          prop="stoptime"
          label="结束时间"
          width="120"
        />
        <el-table-column prop="status" label="状态" width="100">
          <template v-slot="scope">
            <span v-if="scope.row.status==='运行中'" style="color: green">{{ scope.row.status }}</span>
            <span v-else-if="scope.row.status==='用户停止'" style="color: yellow">{{ scope.row.status }}</span>
            <span v-else style="color: red">{{ scope.row.status }}</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="description"
          label="描述"
          min-width="80"
        />
        <el-table-column label="操作" min-width="180">
          <template slot-scope="scope">
            <el-button type="success" size="small" @click="startTask(scope.row.name)">启动</el-button>
            <el-button type="warning" size="small" @click="stopTask(scope.row.name)">停止</el-button>
            <el-button type="primary" size="small" @click="clearAbnormal(scope.row.name)">清除异常</el-button>
            <el-button type="info" size="small" @click="getLog(scope.row.name)">下载log</el-button>
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
      tableData: null
    }
  },
  created() {
    this.getRunningTask()
  },
  methods: {
    getLog(name) {
      name = name.split('.py')[0]
      const url = '/get_log/' + name + '.log'
      this.axios.get(url).then(res => {
        if (res.data.code === 'failed') {
          this.$message({
            message: res.data.msg
          })
        } else {
          const blob = new Blob([res.data])
          const link = document.createElement('a')
          link.download = name
          link.style.display = 'none'
          link.href = URL.createObjectURL(blob)
          document.body.appendChild(link)
          link.click()
          URL.revokeObjectURL(link.href)
          document.body.removeChild(link)
        }
      }).catch(function(error) {
        console.log(error)
      })
    },
    clearAbnormal(name) {
      name = name.split('.py')[0]
      const url = '/remove_abnormal_task/' + name
      this.axios.get(url).then(res => {
        if (res.data.code === 'success') {
          this.$message({
            message: '清除异常任务' + name + '成功',
            type: 'success'
          })
          this.refresh()
        } else {
          this.$message({
            message: '清除异常任务' + name + '失败' + res.data.message,
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
    stopTask(name) {
      const url = '/stop_taskset/' + name
      this.axios.get(url).then(res => {
        if (res.data.code === 'success') {
          this.$message({
            message: '停止任务' + name + '成功',
            type: 'success'
          })
          this.refresh()
        } else {
          this.$message({
            message: '停止任务' + name + '失败',
            type: 'erroe'
          })
        }
      })
    },
    refresh() {
      this.reload()
    },
    getRunningTask() {
      this.axios.get('/show_task_status')
        .then(res => {
          this.tableData = res.data.msg
        })
        .catch(error => {
          console.log(error)
        })
    }
  }
}
</script>
