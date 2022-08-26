# 引入当前所有产品模块!!!一定要显示引用，exec不顶用
from source.locust_methods import Agent_SDN_nolocust
from source.locust_methods import func_instanceName, find_kwargs, timeStap, check, check_res_code, sendto_weixin
from source.CFW_module import CFW
from source.ECS_module import ECS
from source.EIP_module import EIP
from source.ORDER_module import ORDER
from source.PRODUCT_module import PRODUCT
from source.VIP_module import VIP
from source.VPC_module import VPC
from source.VM_module import VM
from source.CCN_module import CCN
from source.NAT_module import NAT
from source.SEC_module import SEC
from source.VPCP_module import VPCP
from source.HAVIP_module import HAVIP
from source.SLB_module import SLB
from source.ENI_module import ENI
from source.HSLB_module import HSLB
from source.BFW_module import BFW
from source.DNS_module import DNS
from source.GSLB_module import GSLB
modules = ['CCN', 'CFW', 'ECS', 'EIP', 'NAT', 'ORDER', 'PRODUCT', 'SEC', 'VIP', 'VM', 'VPC', 'VPCP', 'HAVIP', 'SLB',
           'HSLB', 'ENI', 'BFW','GSLB']
funcs = ['func_instanceName', 'Agent_SDN_nolocust', 'find_kwargs', 'timeStap', 'check', 'check_res_code',
         'sendto_weixin']
__all__ = modules + funcs
