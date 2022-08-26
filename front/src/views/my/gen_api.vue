<template>
  <div class="app-container">
    <div class="refresh">
      <el-row>
        <el-col span="12">
          <el-button class="el-icon-refresh-right" @click="refresh" />
          <el-button @click="clearForm()">重置</el-button>
          <el-button type="primary" @click="genApi()">生成API接口函数</el-button>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="11">
          <el-form
            ref="dataForm"
            :model="apiForm"
            :rules="apiRules"
            style="width: 400px;margin-left: 10px;"
          >
            <el-form-item label="模块名称" prop="api_module_name">
              <el-input v-model="apiForm.api_module_name" type="textarea" :rows="1" />
            </el-form-item>
            <el-form-item label="url" prop="api_url">
              <el-input v-model="apiForm.api_url" type="textarea" :rows="1" />
            </el-form-item>
            <el-form-item label="方法" prop="api_method">
              <el-input v-model="apiForm.api_method" type="textarea" :rows="1" />
            </el-form-item>
            <el-form-item label="载荷" prop="api_data">
              <el-input v-model="apiForm.api_data" type="textarea" :rows="4" />
            </el-form-item>
            <el-form-item label="带默认值的参数" prop="api_args_with_data">
              <el-input v-model="apiForm.api_args_with_data" type="textarea" :rows="4" />
            </el-form-item>
            <el-form-item label="带方法的参数" prop="api_to_edit">
              <el-input v-model="apiForm.api_to_edit" type="textarea" :rows="4" />
            </el-form-item>
            <el-form-item label="接口返回" prop="api_res">
              <el-input v-model="apiForm.api_res" type="textarea" :rows="4" />
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="13">
          <el-form ref="apiFuncForm" :model="apiFuncForm" label-position="left" style="width: 600px;margin-left: 10px;">
            <el-form-item label="接口函数" prop="api_res">
              <el-input v-model="apiFuncForm.api_func_context" type="textarea" :rows="20" />
            </el-form-item>
          </el-form>
        </el-col>
      </el-row>
    </div>
  </div>

</template>

<script>
export default {
  inject: ['reload'],
  data() {
    return {
      apiForm: {
        api_module_name: '',
        api_url: '',
        api_method: '',
        api_data: '',
        api_args_with_data: '',
        api_to_edit: '',
        api_res: ''
      },
      apiFuncForm: {
        api_func_context: ''
      },
      apiRules: {
        api_module_name: [
          { required: true, type: 'string', pattern: /[A-Z]{3,64}/, message: '长度大于3个字符，必须全部为大写', trigger: 'blur' }
        ],
        api_url: [
          {
            required: true,
            type: 'url',

            message: '请输入正确的url',
            trigger: 'blur'
          }
        ],
        api_method: [
          {
            required: true,
            type: 'string',
            pattern: /(get)|(GET)|(post)|(POST)|(delete)|(DELETE)/,
            message: '必须为get|post|delete',
            trigger: 'blur'
          }
        ],
        // 输入应该是字典或者列表
        api_data: [
          {
            required: false,
            pattern: /^[\{\[].+[}\]]$/,
            message: '传入字典或列表,例：{"key":"value"} or ["key1","key2"]',
            trigger: 'blur'
          }
        ],
        api_args_with_data: [
          { required: false, pattern: /^[\{].+[}]$/, message: '传入字典，例:{"regionId":"cd_regin"}', trigger: 'blur' }
        ],
        api_to_edit: [
          {
            required: false,
            pattern: /^[\{].+[}]$/,
            message: '传入字典，例:{"projectId":"self.project_id_(projectId,self.productCode_CFW)"}',
            trigger: 'blur'
          }
        ]
      }
    }
  },
  methods: {
    refresh() {
      this.reload()
    },
    clearForm() {
      this.apiForm = {
        api_module_name: '',
        api_url: '',
        api_data: '',
        api_args_with_data: '',
        api_to_edit: '',
        api_res: ''
      }
      this.apiFuncForm = {
        api_func_context: ''
      }
    },
    genApi() {
      const url = '/gen_api'
      const data = new FormData()
      data.append('module_name', this.apiForm.api_module_name)
      data.append('method', this.apiForm.api_method)
      data.append('url', this.apiForm.api_url)
      data.append('data', this.apiForm.api_data)
      data.append('args_with_data', this.apiForm.api_args_with_data)
      data.append('to_edit', this.apiForm.api_to_edit)
      data.append('res', this.apiForm.api_res)
      const _data = JSON.stringify(Object.fromEntries(data))
      this.axios({
        method: 'post',
        url: url,
        headers: {
          'Content-Type': 'application/json;charset=UTF-8'
        },
        data: _data
      }).then(res => {
        if (res.data.code === 'success') {
          this.fillApiFuncForm(res.data.context)
        } else {
          this.$message({
            message: res.data.msg,
            type: 'error'
          })
        }
      })
    },
    fillApiFuncForm(context) {
      this.apiFuncForm.api_func_context = context
    }
  }
}
</script>

