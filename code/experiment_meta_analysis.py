"""
experiment_meta_analysis.py

This script analyzes multiple runs of an experiment, aggregating results by simulation type
and providing comparative analysis across different parameter configurations.
"""

import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import re

class ExperimentAnalyzer:
    def __init__(self, experiment_path):
        self.base_path = Path(experiment_path)
        self.experiment_name = self.base_path.name
        
    def _get_sim_groups(self):
        """Group simulation directories by base simulation name"""
        sim_paths = [p for p in self.base_path.iterdir() if p.is_dir()]
        sim_groups = {}
        
        for path in sim_paths:
            # Extract base sim name (e.g., "debt_aware_sim" from "debt_aware_sim_run0_2025-01-12")
            base_name = re.match(r'([^_]+(?:_[^_]+)*?)_run\d+', path.name)
            if base_name:
                base_name = base_name.group(1)
                sim_groups.setdefault(base_name, []).append(path)
        
        return sim_groups
    
    def analyze_experiment(self):
        """Analyze all simulations in the experiment, grouped by simulation type"""
        results = {
            'experiment_name': self.experiment_name,
            'timestamp': datetime.now().isoformat(),
            'sims': []
        }
        
        sim_groups = self._get_sim_groups()
        
        # Analyze each simulation type
        for sim_name, sim_paths in sim_groups.items():
            sim_results = self._analyze_sim_group(sim_name, sim_paths)
            results['sims'].append(sim_results)
            
        return results
    
    def _analyze_sim_group(self, sim_name, sim_paths):
        """Analyze all runs of a particular simulation type, producing a single summary"""
        # Collect all initial and final states
        initial_states = []
        final_states = []
        
        for path in sim_paths:
            census_df = pd.read_csv(path / 'census.csv')
            initial_states.append({
                'num_firms': float(census_df.iloc[0]['num_firms']),
                'num_singleton_firms': float(census_df.iloc[0]['num_singleton_firms']),
                'employment_rate': float(census_df.iloc[0]['employment_rate']),
                'wealth_q0': float(census_df.iloc[0]['wealth_q0']),
                'wealth_q20': float(census_df.iloc[0]['wealth_q20']),
                'wealth_q40': float(census_df.iloc[0]['wealth_q40']),
                'wealth_q60': float(census_df.iloc[0]['wealth_q60']),
                'wealth_q80': float(census_df.iloc[0]['wealth_q80']),
                'wealth_q100': float(census_df.iloc[0]['wealth_q100']),
                'wealth_gini': float(census_df.iloc[0]['wealth_gini']),
                'wage_gini': float(census_df.iloc[0]['wage_gini']),
                'utility_gini': float(census_df.iloc[0]['utility_gini']),
                'debt_to_savings': float(census_df.iloc[0]['debt_to_savings'])
            })
            final_states.append({
                'num_firms': float(census_df.iloc[-1]['num_firms']),
                'num_singleton_firms': float(census_df.iloc[-1]['num_singleton_firms']),
                'employment_rate': float(census_df.iloc[-1]['employment_rate']),
                'wealth_q0': float(census_df.iloc[-1]['wealth_q0']),
                'wealth_q20': float(census_df.iloc[-1]['wealth_q20']),
                'wealth_q40': float(census_df.iloc[-1]['wealth_q40']),
                'wealth_q60': float(census_df.iloc[-1]['wealth_q60']),
                'wealth_q80': float(census_df.iloc[-1]['wealth_q80']),
                'wealth_q100': float(census_df.iloc[-1]['wealth_q100']),
                'wealth_gini': float(census_df.iloc[-1]['wealth_gini']),
                'wage_gini': float(census_df.iloc[-1]['wage_gini']),
                'utility_gini': float(census_df.iloc[-1]['utility_gini']),
                'debt_to_savings': float(census_df.iloc[-1]['debt_to_savings']),
                'largest_firm_size': float(census_df.iloc[-1]['largest_firm_size']),
                'avg_firm_size': float(census_df.iloc[-1]['avg_firm_size'])
            })
        
        # Calculate averages across all runs
        initial_df = pd.DataFrame(initial_states)
        final_df = pd.DataFrame(final_states)
        
        return {
            'sim_name': sim_name,
            'runs': len(sim_paths),
            'run_summary': {
                'average_initial_state': initial_df.mean().to_dict(),
                'average_final_state': final_df.mean().to_dict()
            }
        }
    
    def generate_report(self, output_path=None):
        """Generate analysis report and save to file"""
        results = self.analyze_experiment()
        
        if output_path is None:
            output_path = self.base_path / f'meta_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze experiment results')
    parser.add_argument('experiment_path', help='Path to experiment directory')
    parser.add_argument('--output', '-o', help='Output path for analysis results')
    args = parser.parse_args()
    
    analyzer = ExperimentAnalyzer(args.experiment_path)
    analyzer.generate_report(args.output)

if __name__ == "__main__":
    main()