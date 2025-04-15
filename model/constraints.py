from collections import defaultdict
from datetime import timedelta

class Constraints:
    @staticmethod
    def resource_capacity_constraint(model, vars, data):
        # Constraint 2: Time-Aware Resource Capacity (Custom Day-by-Day Tracking)
        # Precollect all preassigned project IDs globally
        global_assigned_project_ids = {
            p['project_id']
            for r in data['resources']
            for p in r.get('active_projects', []) if p.get("status", "").strip().lower() != "on hold"
        }
    
        on_hold_project_ids = {
            p['project_id']
            for r in data['resources']
            for p in r.get('active_projects', []) if p.get("status", "").strip().lower() == "on hold"
        }
    
        print(f"[Debug] Globally assigned projects (non-on-hold): {sorted(global_assigned_project_ids)}")
        print(f"[Debug] On-hold projects: {sorted(on_hold_project_ids)}")
    
        project_selection_vars = []
        project_assignment_vars = defaultdict(list)
    
        for r_idx, resource in enumerate(data['resources']):
            capacity = resource.get('project_capacity', 1)
            print(f"\n--- Resource: {resource['name']} (capacity {capacity}) ---")
    
            resource_intervals = []
            assigned_ids = []
    
            for active in resource.get('active_projects', []):
                status = active.get("status", "").strip().lower()
                project_id = active['project_id']
    
                project = next((p for p in data['projects'] if p['project_id'] == project_id), None)
                if not project:
                    continue
                
                if status == "on hold":
                    print(f"[Skip - On Hold] {resource['name']} → {project_id}")
                    data.setdefault('_on_hold_projects', defaultdict(list))[resource['name']].append(project)
                    continue
                
                start = vars['days_from_global'](project['start_date'])
                duration = (project['end_date'] - project['start_date']).days + 1
                end = start + duration
    
                print(f"[Fixed - Preassigned] {resource['name']} → {project_id} from {project['start_date'].strftime('%Y-%m-%d')} to {project['end_date'].strftime('%Y-%m-%d')}, duration {duration}")
    
                start_var = model.NewConstant(start)
                duration_var = model.NewConstant(duration)
                end_var = model.NewConstant(end)
    
                interval = model.NewIntervalVar(start_var, duration_var, end_var, f"{project_id}_fixed_interval_{resource['name']}")
                resource_intervals.append(interval)
    
                model.Add(vars['project_resources'][project_id] == r_idx)
                model.Add(vars['project_starts'][project_id] == start)
    
                assigned_const = model.NewConstant(1)
                project_assignment_vars[project_id].append(assigned_const)
                assigned_ids.append(project_id)
    
            for project in data['projects']:
                project_id = project['project_id']
                if project_id in global_assigned_project_ids or project_id in on_hold_project_ids:
                    continue
                
                resource_var = vars['project_resources'][project_id]
                start_var = vars['project_starts'][project_id]
                duration = project['duration']
                start_day = vars['days_from_global'](project['start_date'])
    
                model.Add(start_var == start_day)
    
                is_assigned = model.NewBoolVar(f"is_assigned_{project_id}_{resource['name']}")
                project_selection_vars.append(is_assigned)
                project_assignment_vars[project_id].append(is_assigned)
    
                model.Add(resource_var == r_idx).OnlyEnforceIf(is_assigned)
                model.Add(resource_var != r_idx).OnlyEnforceIf(is_assigned.Not())
    
                end_var = model.NewIntVar(0, vars['horizon'], f"{project_id}_end_{resource['name']}")
                model.Add(end_var == start_var + duration)
    
                interval = model.NewOptionalIntervalVar(start_var, duration, end_var, is_assigned, f"{project_id}_interval_{resource['name']}")
                resource_intervals.append(interval)
    
                print(f"[Candidate Check] {resource['name']} → {project_id} candidate duration {duration} ({project['start_date'].strftime('%Y-%m-%d')} to {project['end_date'].strftime('%Y-%m-%d')})")
                print(f"[Optional - Solver-assigned] {resource['name']} → {project_id} from {project['start_date'].strftime('%Y-%m-%d')} to {project['end_date'].strftime('%Y-%m-%d')}, duration {duration}")
    
            print(f"[Capacity Debug] {resource['name']} → active (not on-hold): {len(resource_intervals)} / capacity: {capacity}")
            if resource_intervals:
                demands = [1] * len(resource_intervals)
                model.AddCumulative(resource_intervals, demands, capacity)
    
        for project_id, assignment_vars in project_assignment_vars.items():
            model.AddAtMostOne(assignment_vars)
            if not any('is_assigned' in var.Name() for var in assignment_vars):
                print(f"[No Valid Assignment] {project_id} → No resource could be assigned this project")
    
        model.Maximize(sum(project_selection_vars))
