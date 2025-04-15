from ortools.sat.python import cp_model
from datetime import datetime

def create_model(data):
    model = cp_model.CpModel()
    vars = {
        'project_starts': {},
        'project_ends': {},
        'project_resources': {},
        'intervals': {}
    }

    # Compute global planning range
    all_dates = [p['start_date'] for p in data['projects']] + [p['end_date'] for p in data['projects']]
    data['min_date'] = min(all_dates)
    data['max_date'] = max(all_dates)
    vars['horizon'] = (data['max_date'] - data['min_date']).days

    # Compute durations
    for project in data['projects']:
        project['duration'] = (project['end_date'] - project['start_date']).days

    # Convert date to offset (from min_date)
    def days_from_global(date):
        return (date - data['min_date']).days

    vars['days_from_global'] = days_from_global

    for project in data['projects']:
        project_id = project['project_id']
        duration = project['duration']

        start_var = model.NewIntVar(0, vars['horizon'], f'start_{project_id}')
        end_var = model.NewIntVar(0, vars['horizon'], f'end_{project_id}')
        interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{project_id}')
        resource_var = model.NewIntVar(0, len(data['resources']) - 1, f'resource_{project_id}')

        vars['project_starts'][project_id] = start_var
        vars['project_ends'][project_id] = end_var
        vars['project_resources'][project_id] = resource_var
        vars['intervals'][project_id] = interval_var

    return model, vars, data['min_date']
