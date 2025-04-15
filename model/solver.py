from ortools.sat.python import cp_model
from datetime import timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch

def solve_model(model, vars, data, global_start):
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("Solution found:\n")

        resource_assignments = defaultdict(list)
        project_dates = {p['project_id']: (p['start_date'], p['end_date']) for p in data['projects']}

        on_hold_ids = {
            p['project_id']
            for r in data['resources']
            for p in r.get('active_projects', [])
            if p.get("status", "").strip().lower() == "on hold"
        }

        # Keep track of already added project IDs
        assigned_project_ids = set()

        for project in data['projects']:
            project_id = project['project_id']
            start_day = solver.Value(vars['project_starts'][project_id])
            end_day = solver.Value(vars['project_ends'][project_id])
            resource_idx = solver.Value(vars['project_resources'][project_id])
            resource_name = data['resources'][resource_idx]['name']

            # Determine label
            label = "[Optional - Solver-assigned]"
            for proj in data['resources'][resource_idx].get('active_projects', []):
                if proj['project_id'] == project_id:
                    status = proj.get("status", "").strip().lower()
                    label = "[Fixed - On Hold]" if status == "on hold" else "[Fixed - Preassigned]"
                    break

            # If it's on hold but reassigned (which shouldn't happen), skip
            if project_id in on_hold_ids and "Optional" in label:
                continue

            start_date = global_start + timedelta(days=start_day)
            end_date = global_start + timedelta(days=end_day)

            resource_assignments[resource_name].append({
                'project_id': project_id,
                'start_day': start_day,
                'start_date': start_date,
                'end_date': end_date,
                'label': label
            })

            assigned_project_ids.add(project_id)

        # Add back on-hold projects skipped from modeling for completeness
        for resource in data['resources']:
            resource_name = resource['name']
            for p in resource.get('active_projects', []):
                project_id = p['project_id']
                if project_id in on_hold_ids and project_id not in assigned_project_ids:
                    raw_start, raw_end = project_dates.get(project_id, (None, None))
                    resource_assignments[resource_name].append({
                        'project_id': project_id,
                        'start_day': float('inf'),
                        'start_date': raw_start,
                        'end_date': raw_end,
                        'label': "[Fixed - On Hold]"
                    })

        # Output
        total_projects = 0
        for resource in sorted(resource_assignments.keys()):
            projects = sorted(resource_assignments[resource], key=lambda x: x['start_day'])
            print(f"\nResource: {resource} ({len(projects)} project(s))")
            for p in projects:
                print(f"  {p['label']} Project {p['project_id']} → {p['start_date'].strftime('%Y-%m-%d')} to {p['end_date'].strftime('%Y-%m-%d')}")
                total_projects += 1

        print(f"\nTotal projects scheduled or pre-assigned: {total_projects}")

        # Gantt Chart
        fig, ax = plt.subplots(figsize=(12, 6))
        y_ticks = []
        y_labels = []
        colors = {
            "[Optional - Solver-assigned]": "tab:blue",
            "[Fixed - Preassigned]": "tab:green",
            "[Fixed - On Hold]": "tab:red"
        }

        y = 0
        for resource in sorted(resource_assignments.keys()):
            for p in sorted(resource_assignments[resource], key=lambda x: x['start_day']):
                start = mdates.date2num(p['start_date'])
                end = mdates.date2num(p['end_date'])
                ax.barh(y, end - start, left=start, color=colors.get(p['label'], 'gray'))
                ax.text(start, y, f"Proj {p['project_id']}", va='center', ha='left', fontsize=8)
                y_labels.append(f"{resource}")
                y_ticks.append(y)
                y += 1

        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xlabel("Date")
        plt.ylabel("Resources")
        plt.title("Project Assignment Gantt Chart")
        plt.grid(True)

        # Add color legend
        legend_elements = [Patch(facecolor=color, label=label) for label, color in colors.items()]
        ax.legend(handles=legend_elements, title="Assignment Type", loc='upper right')

        plt.tight_layout()
        plt.show(block=True)
    else:
        print("No solution found.")
