# example_1_create_project

这个实例是为了测试能量流优化模型，在模型中使用单纯的能量流

案例介绍：

建筑为办公楼，面积为200平米，电需求曲线和热需求曲线由默认方法生成，热总需求：22460 kWh；电总需求：6390 kWh；热峰值：25.43 kW；电峰值：2.97 kW

计算步长为8760小时。可选择的设备有

![Untitled](example_1_create_project%2001c79552292546cabef4bd897490213d/Untitled.png)

- 求解时发现模型为非凸模型，计算时间很长，查找非凸来源
    
    来源是17520个二次方限制条件（刚好是8760的两倍，但是只找到一个方程中含有二次方限制条件），新的heatpump模型里面cop被定义为变量，（实际是按照气温出来的定值）
    
    cop修正为Parameter之后为LP问题，计算时间很快
    
- 结果分析
    
    设备边界条件：
    
    heatpump: 1-100 kW， cop：2.3-4.3
    
    water_tes: 40 kWh，最大放热功率80 kW
    
    therm_cns: 1000 kW
    
    其他设备: 0-100
    
    pv：价格1000，效率0.18，
    
    battery: loss每小时10%损耗，充放效率都为0.99，价格1000， init soc等于0.5
    
    优化结果：
    
    The size of size_solar_coll is 100.0，显示input功率最大大概为2kW，output功率最大约为0.35，这里符合效率18%的设备信息，问题来源是cost设置为0，导致选型结果为100.
    The size of size_gas_grid is 100.0
    The size of size_bat is 0.0
    The size of size_e_boi is 4.823266204691196
    The size of size_heat_pump is 1.0
    The size of size_e_grid is 100.0
    The size of size_water_tes is 40.0，原来的计算方式以及单位都是kWh，新版本更改为2000升，等效于139 kWh，价格更改为1800欧每立方米，数值需要后期修改
    The size of size_boi is 18.804377639765587
    The size of size_pv is 4.5 kwp，最大输出约为3.4kW，20平米
    
    annual cost为5001.58
    
    Optimal objective  4.934473912e+03
    The size of project without loss:
    The size of porject with loss:
    The size of size_gas_grid is 100.0
    The size of size_e_grid is 100.0
    The size of size_pv is 3.6
    The size of size_water_tes is 40.0
    The size of size_e_boi is 4.85096662648934
    The size of size_solar_coll is 0.0
    The size of size_heat_pump is 1.0
    The size of size_boi is 18.812951434896746
    The size of size_bat is 0.0