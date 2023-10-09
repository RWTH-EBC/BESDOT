# 导入所需的库和模块
import os
import warnings
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy
import pandas as pd

# 设置了一个很小的常量
small_nr = 0.00001

script_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_folder, '../..', 'data', 'subsidy', 'Bundesregierung_EEG.csv')
subsidy_data = pd.read_csv(csv_file_path)


# 这是一个EEG类的定义，它继承自Subsidy类。在类的构造方法__init__中初始化了一些属性，包括name、components、type等，
# 还调用了父类 Subsidy 的构造方法，并设置了feed_type和tariff_rate。
class EEG(Subsidy):
    def __init__(self, feed_type, tariff_rate):
        super().__init__(enact_year=2023)
        self.name = 'EEG'
        self.components = ['PV']
        self.type = 'operate'
        self.energy_pair = []
        self.subsidy_data = subsidy_data
        self.feed_type = feed_type  # Preserving Customer Choice
        self.tariff_rate = tariff_rate  # Preserving Customer Choice

    # 这个方法用于分析建筑的拓扑信息，以确定光伏和电网之间的连接。遍历了building对象的拓扑信息，
    # 如果找到了光伏和电网的连接，就将它们添加到 energy_pair 属性中。如果没有找到连接，会发出一个警告。
    def analyze_topo(self, building):
        pv_name = None
        e_grid_name = None
        for index, item in building.topology.iterrows():
            if item["comp_type"] == "PV":
                pv_name = item["comp_name"]
            elif item["comp_type"] == "ElectricityGrid":
                e_grid_name = item["comp_name"]
        if pv_name is not None and e_grid_name is not None:
            self.energy_pair.append([pv_name, e_grid_name])
        else:
            warnings.warn("Not found PV name or electricity grid name.")

    # 这个方法用于向模型中添加约束。首先根据energy_pair以及模型的组件名找到光伏和电网相关的模型组件。
    # 然后添加一个约束，确保总电网流量等于每个时间步的电网流量之和。
    # 接着，遍历补贴数据的每一行，检查当前行的"Feed Type"是否与客户选择的feed_type相符。
    # 如果相符，根据客户选择的tariff_rate选择适当的补贴率，并创建约束和不等式。
    def add_cons(self, model):
        pv_grid_flow = model.find_component('elec_' + self.energy_pair[
            0][0] + '_' + self.energy_pair[0][1])
        pv_grid_total = model.find_component('subsidy_' + self.name +
                                             '_PV_energy')
        pv_size = model.find_component('size_' + self.energy_pair[0][0])
        subsidy = model.find_component('subsidy_' + self.name + '_PV')

        model.cons.add(pv_grid_total == sum(pv_grid_flow[t] for t in model.time_step))

        for idx, row in self.subsidy_data.iterrows():
            if row['Feed Type'] == self.feed_type:  # 检查当前行的 "Feed Type" 是否与客户选择相符
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']

                # Select the correct tariff rate based on the customer's choice
                if self.tariff_rate == 'Direkte Vermarktung':
                    subsidy_rate = row['Direkte Vermarktung']
                elif self.tariff_rate == 'Feste Verguetung':
                    subsidy_rate = row['Feste Verguetung']
                else:
                    raise ValueError("Invalid tariff rate selected")

                tariff = Disjunct()

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=pv_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=pv_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=pv_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == pv_grid_total * subsidy_rate)

                tariff_name = self.name + '_tariff_' + str(idx)
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        # 创建包含所有tariff选项的Disjunction。
        # 这部分代码用于创建一个Disjunction，其中包括根据客户选择的feed_type构建的所有补贴选项。它遍历补贴数据的每一行，
        # 如果"Feed Type"与客户选择相符，则将对应的Disjunct加入到Disjunction中。
        tariff_disjunction_expr = [model.find_component(f'{self.name}_tariff_{idx}') for idx, row
                                   in self.subsidy_data.iterrows() if row['Feed Type'] == self.feed_type]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_subsidy_{self.name}', dj_subsidy)

    # 这个方法用于向模型中添加变量。首先调用了父类Subsidy的add_vars方法，
    # 然后创建一个名为 'subsidy_' + self.name + '_PV_energy' 的变量，表示光伏电量的补贴。
    def add_vars(self, model):
        super().add_vars(model)

        total_energy = pyo.Var(bounds=(0, 10 ** 10))
        model.add_component(f'subsidy_{self.name}_PV_energy', total_energy)

