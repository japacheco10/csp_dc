from model import create_model, solve_model, Constraints
from common import Utils
import os

if __name__ == '__main__':
    Utils.init(os.path.dirname(__file__))
    projects_data, resources_data, holidays_data = Utils.load_data()
    if projects_data and resources_data and holidays_data:
        data = {
            'projects': projects_data['projects'],
            'resources': resources_data['resources'],
            'holidays': holidays_data['holidays']
        }

        # Create model will add first constraint, one resource per project
        model, vars, global_start = create_model(data)

        # Add constraint group(s)
        Constraints.resource_capacity_constraint(model, vars, data)

        # Solve
        solve_model(model, vars, data, global_start)
