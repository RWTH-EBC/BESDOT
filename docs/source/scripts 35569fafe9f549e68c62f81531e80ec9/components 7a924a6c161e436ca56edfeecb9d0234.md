# components

这个文件夹中储存的是细化的各个能源设备模型

### UnderfloorHeat.py

这个类用于生成地暖模型，可以考虑是否添加用户舒适度模型

**限制条件**

- _constraint_conver: energy conversion equation. 能量转化方程
作为终端设备看作效率为1，输入能量等于输出能量。
- _constraint_temp：进水水温的限制条件
只有在外界气温低于规定的开启温度时才会开启，否则在无热需求的时候添加了限制条件，是无意义的；
可以是进水水温是恒定的模型，默认情况是恒定；
也可以是进水水温有上下限的模型。
- _constraint_return_temp:回水水温的限制条件
无限制条件，确认后可删
- _constraint_floor_temp：
- _constraint_pmv
- _constraint_heat_water_return_temp
- _constraint_heat_inputs：继承FluidComponent的方法，将输入能量与流入的水流的温度和流量关联起来
- _constraint_vdi2067：继承Component的方法，计算年化成本的方法

### Storage

这个类作为所有储能设备的父类，考虑了能量的储存和释放效率，每小时的自耗，最大的充放功率。

还有两个特殊的假定条件：

1. 在整个模拟前后的能量保持不变，一方面可以减少优化结果初期装满能量，结束时能量耗尽，这样情况不利于现实情况的分析；另一方面放置在选型中选择过大的储能装置，这个假定条件一直都会是被添加状态
2. 在cluster之后的典型周期内能量保持不变，一般是24小时，这个假定条件一般是不开启状态，需要分析cluster带来的影响后再决定

**属性**

- input_efficiency， 默认为1
- output_efficiency， 默认为1
- max_soc， 默认为1
- min_soc， 默认为0
- init_soc， 默认为0.5
- e2p_in， 默认为0.5
- e2p_out， 默认为0.5
- loss， 默认为0.01

**限制条件**

- _constraint_conver：能量转换方程，考虑了充放效率和每个步长的能量损失
- _constraint_init_energy：初始状态对应限制条件，hard code为不添加，可以改为添加的版本
- _constraint_maxpower：最大充放速度限制条件
- _constraint_maxcap：最大和最小容量限制条件，一般限制为最大
- _constraint_conserve：对应假定条件(2)
- _constriant_unchange：对应假定条件(1)

### HotWaterStorage

Topology中Storage中的size变量是能量，单位是kWh，而HotWaterStorage是m³，这一点需要注意。结果中size仍是kwh为单位，体积的变量是volume