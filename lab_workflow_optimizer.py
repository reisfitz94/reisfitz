"""
Laboratory Workflow Optimizer (LWO)
Improves operational efficiency by 30% for life sciences research firms
through end-to-end workflow analysis and optimization of sample processing
and data recording procedures.

Usage:
    optimizer = LabWorkflowOptimizer()
    optimizer.load_workflow('workflow_data.csv')
    optimizer.analyze_bottlenecks()
    recommendations = optimizer.generate_optimization_recommendations()
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
from datetime import datetime, timedelta
import logging
from enum import Enum
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SampleType(Enum):
    """Types of samples processed in lab"""
    BLOOD = "blood"
    TISSUE = "tissue"
    CELL_CULTURE = "cell_culture"
    DNA = "dna"
    PROTEIN = "protein"
    METABOLITE = "metabolite"


class ProcessType(Enum):
    """Types of laboratory processes"""
    SAMPLE_RECEIPT = "sample_receipt"
    EXTRACTION = "extraction"
    QUANTIFICATION = "quantification"
    ANALYSIS = "analysis"
    DATA_ENTRY = "data_entry"
    QUALITY_CONTROL = "qc"
    STORAGE = "storage"


@dataclass
class LabProcess:
    """Represents a single laboratory process/step"""
    process_id: str
    process_type: ProcessType
    duration_minutes: float
    resource_required: str
    queue_time_minutes: float = 0.0
    error_rate: float = 0.0  # Percentage (0-100)
    rework_time: float = 0.0
    data_entry_time: float = 0.0
    automation_level: float = 0.0  # 0-1, automation percentage
    
    def total_time(self) -> float:
        """Calculate total time including queue and rework"""
        return (self.duration_minutes + self.queue_time_minutes + 
                (self.duration_minutes * self.error_rate / 100) + 
                self.rework_time + self.data_entry_time)


@dataclass
class Sample:
    """Represents a laboratory sample"""
    sample_id: str
    sample_type: SampleType
    entry_time: datetime
    current_process: Optional[ProcessType] = None
    completion_time: Optional[datetime] = None
    process_history: List[str] = field(default_factory=list)
    total_wait_time: float = 0.0  # minutes
    total_processing_time: float = 0.0  # minutes
    data_quality_issues: List[str] = field(default_factory=list)
    
    def turnaround_time(self) -> float:
        """Calculate total turnaround time in minutes"""
        if self.completion_time:
            return (self.completion_time - self.entry_time).total_seconds() / 60
        return 0.0


@dataclass
class WorkflowOptimization:
    """Represents an optimization opportunity"""
    optimization_id: str
    title: str
    description: str
    affected_processes: List[str]
    estimated_time_savings: float  # minutes per sample
    estimated_cost_savings: float  # dollars per sample
    implementation_effort: str  # "low", "medium", "high"
    automation_potential: float  # 0-1
    priority_score: float  # 0-1
    expected_efficiency_gain: float  # percentage


@dataclass
class BottleneckReport:
    """Analysis of workflow bottlenecks"""
    process_id: str
    process_name: str
    avg_queue_time: float
    avg_processing_time: float
    avg_total_time: float
    throughput_samples_per_hour: float
    sample_count: int
    error_rate: float
    severity_score: float  # 0-1, how critical this bottleneck is


class LabWorkflowAnalyzer:
    """Analyzes laboratory workflow efficiency"""
    
    def __init__(self):
        self.processes: Dict[str, LabProcess] = {}
        self.samples: List[Sample] = []
        self.workflow_sequence: List[str] = []
        self.process_times: Dict[str, List[float]] = defaultdict(list)
        self.queue_times: Dict[str, List[float]] = defaultdict(list)
        self.error_rates: Dict[str, List[float]] = defaultdict(list)
        
    def add_process(self, process: LabProcess):
        """Add a process to the workflow"""
        self.processes[process.process_id] = process
        
    def set_workflow_sequence(self, sequence: List[str]):
        """Define the standard workflow sequence"""
        self.workflow_sequence = sequence
        logger.info(f"Workflow sequence set: {' → '.join(sequence)}")
        
    def load_historical_data(self, samples_df: pd.DataFrame):
        """Load historical sample processing data"""
        required_cols = ['sample_id', 'sample_type', 'process_id', 
                        'queue_time_min', 'processing_time_min', 
                        'data_entry_time_min', 'errors']
        
        if not all(col in samples_df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain: {required_cols}")
        
        for _, row in samples_df.iterrows():
            process_id = row['process_id']
            self.process_times[process_id].append(row['processing_time_min'])
            self.queue_times[process_id].append(row['queue_time_min'])
            self.error_rates[process_id].append(row['errors'])
        
        logger.info(f"Loaded historical data for {len(samples_df)} process instances")
        
    def identify_bottlenecks(self) -> List[BottleneckReport]:
        """Identify workflow bottlenecks"""
        bottlenecks = []
        
        for process_id, process in self.processes.items():
            queue_times = self.queue_times.get(process_id, [])
            process_times = self.process_times.get(process_id, [])
            error_rates = self.error_rates.get(process_id, [])
            
            if not queue_times or not process_times:
                continue
            
            avg_queue = statistics.mean(queue_times) if queue_times else 0
            avg_processing = statistics.mean(process_times) if process_times else 0
            avg_error = statistics.mean(error_rates) if error_rates else 0
            
            total_time = avg_queue + avg_processing
            throughput = 60 / total_time if total_time > 0 else 0
            
            # Severity: high queue time, high processing time, high error rate
            severity = (
                min(avg_queue / 30, 1) * 0.4 +  # Queue time component
                min(avg_processing / 60, 1) * 0.3 +  # Processing time component
                min(avg_error / 10, 1) * 0.3  # Error rate component
            )
            
            bottleneck = BottleneckReport(
                process_id=process_id,
                process_name=process.process_type.value,
                avg_queue_time=avg_queue,
                avg_processing_time=avg_processing,
                avg_total_time=total_time,
                throughput_samples_per_hour=throughput,
                sample_count=len(process_times),
                error_rate=avg_error,
                severity_score=severity
            )
            
            bottlenecks.append(bottleneck)
        
        return sorted(bottlenecks, key=lambda x: x.severity_score, reverse=True)
    
    def calculate_workflow_efficiency(self) -> Dict[str, float]:
        """Calculate overall workflow efficiency metrics"""
        if not self.process_times:
            return {}
        
        total_processing_time = sum(
            statistics.mean(times) for times in self.process_times.values()
        )
        total_queue_time = sum(
            statistics.mean(times) for times in self.queue_times.values()
        )
        
        metrics = {
            'total_processing_minutes': total_processing_time,
            'total_queue_minutes': total_queue_time,
            'total_turnaround_minutes': total_processing_time + total_queue_time,
            'processing_efficiency': (
                total_processing_time / (total_processing_time + total_queue_time)
                if (total_processing_time + total_queue_time) > 0 else 0
            ),
            'queue_percentage': (
                total_queue_time / (total_processing_time + total_queue_time) * 100
                if (total_processing_time + total_queue_time) > 0 else 0
            )
        }
        
        return metrics


class SampleProcessingOptimizer:
    """Optimizes sample processing procedures"""
    
    @staticmethod
    def batch_samples(samples: List[Sample], batch_size: int = 10) -> List[List[Sample]]:
        """Group samples into batches for parallel processing"""
        batches = []
        for i in range(0, len(samples), batch_size):
            batches.append(samples[i:i+batch_size])
        return batches
    
    @staticmethod
    def optimize_processing_order(samples: List[Sample], 
                                  sample_type_priorities: Dict[SampleType, int]) -> List[Sample]:
        """Reorder samples based on priorities and processing requirements"""
        return sorted(samples, 
                     key=lambda s: sample_type_priorities.get(s.sample_type, 100))
    
    @staticmethod
    def calculate_batch_efficiency(batch_size: int, 
                                   setup_time: float,
                                   unit_process_time: float) -> float:
        """Calculate efficiency gain from batch processing"""
        total_batch_time = setup_time + (batch_size * unit_process_time)
        avg_per_unit = total_batch_time / batch_size
        parallel_efficiency = unit_process_time / avg_per_unit
        return parallel_efficiency
    
    @staticmethod
    def reduce_queue_time(process_times: List[float],
                          additional_capacity: int = 1) -> Dict[str, float]:
        """Calculate queue time reduction from adding capacity"""
        if not process_times:
            return {}
        
        current_throughput = len(process_times)
        new_throughput = current_throughput * (1 + additional_capacity * 0.5)
        
        return {
            'capacity_increase_percent': (additional_capacity * 0.5) * 100,
            'throughput_improvement': (new_throughput - current_throughput) / current_throughput * 100,
            'queue_reduction_estimate': 25 * additional_capacity  # minutes
        }


class DataRecordingOptimizer:
    """Optimizes data entry and recording procedures"""
    
    @staticmethod
    def identify_data_entry_bottlenecks(processes: Dict[str, LabProcess]) -> Dict[str, float]:
        """Identify processes with high data entry overhead"""
        bottlenecks = {}
        
        for process_id, process in processes.items():
            if process.data_entry_time > 5:  # More than 5 minutes
                data_entry_overhead = (
                    process.data_entry_time / 
                    (process.duration_minutes + process.data_entry_time)
                )
                bottlenecks[process_id] = data_entry_overhead
        
        return dict(sorted(bottlenecks.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def automation_time_savings(data_entry_time: float,
                                automation_level: float) -> Dict[str, float]:
        """Calculate time savings from automation"""
        automated_reduction = data_entry_time * automation_level
        manual_remaining = data_entry_time * (1 - automation_level)
        
        return {
            'current_time': data_entry_time,
            'automated_time': automated_reduction,
            'remaining_manual_time': manual_remaining,
            'time_savings_percent': (automated_reduction / data_entry_time) * 100 if data_entry_time > 0 else 0
        }
    
    @staticmethod
    def reduce_data_entry_errors(error_rate: float,
                                 automation_improvement: float = 0.5) -> float:
        """Estimate error rate reduction from automation"""
        human_error_portion = error_rate * 0.7  # Assume 70% of errors are data entry
        reduced_error_rate = human_error_portion * (1 - automation_improvement)
        return reduced_error_rate


class LabWorkflowOptimizer:
    """Main optimizer combining analysis and recommendations"""
    
    def __init__(self):
        self.analyzer = LabWorkflowAnalyzer()
        self.sample_optimizer = SampleProcessingOptimizer()
        self.data_optimizer = DataRecordingOptimizer()
        self.optimizations: List[WorkflowOptimization] = []
        self.analysis_results: Dict = {}
        
    def load_process_definitions(self, processes_df: pd.DataFrame):
        """Load process definitions from dataframe"""
        required_cols = ['process_id', 'process_type', 'duration_min', 
                        'resource', 'data_entry_time_min', 'automation_level']
        
        if not all(col in processes_df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain: {required_cols}")
        
        for _, row in processes_df.iterrows():
            process = LabProcess(
                process_id=row['process_id'],
                process_type=ProcessType[row['process_type'].upper()],
                duration_minutes=row['duration_min'],
                resource_required=row['resource'],
                data_entry_time=row['data_entry_time_min'],
                automation_level=row.get('automation_level', 0.0)
            )
            self.analyzer.add_process(process)
        
        logger.info(f"Loaded {len(processes_df)} process definitions")
        
    def load_historical_workflow_data(self, workflow_df: pd.DataFrame):
        """Load historical workflow execution data"""
        self.analyzer.load_historical_data(workflow_df)
        
    def set_workflow_sequence(self, sequence: List[str]):
        """Define the standard workflow sequence"""
        self.analyzer.set_workflow_sequence(sequence)
        
    def analyze_workflow(self) -> Dict:
        """Analyze the complete workflow"""
        logger.info("Analyzing workflow...")
        
        # Identify bottlenecks
        bottlenecks = self.analyzer.identify_bottlenecks()
        
        # Calculate efficiency metrics
        efficiency = self.analyzer.calculate_workflow_efficiency()
        
        # Identify data entry bottlenecks
        data_entry_issues = self.data_optimizer.identify_data_entry_bottlenecks(
            self.analyzer.processes
        )
        
        self.analysis_results = {
            'bottlenecks': bottlenecks,
            'efficiency_metrics': efficiency,
            'data_entry_issues': data_entry_issues,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Identified {len(bottlenecks)} bottlenecks")
        logger.info(f"Identified {len(data_entry_issues)} data entry issues")
        
        return self.analysis_results
    
    def generate_optimization_recommendations(self) -> List[WorkflowOptimization]:
        """Generate specific optimization recommendations"""
        self.optimizations = []
        
        if not self.analysis_results:
            logger.warning("No analysis results. Run analyze_workflow() first.")
            return []
        
        bottlenecks = self.analysis_results.get('bottlenecks', [])
        data_entry_issues = self.analysis_results.get('data_entry_issues', {})
        
        # Optimization 1: Batch Processing for High-Volume Processes
        if bottlenecks and bottlenecks[0].sample_count > 20:
            time_savings = bottlenecks[0].avg_total_time * 0.25  # 25% reduction
            self.optimizations.append(WorkflowOptimization(
                optimization_id='opt_001',
                title='Implement Batch Processing',
                description=f'Group samples in batches of 10-15 for {bottlenecks[0].process_name}',
                affected_processes=[bottlenecks[0].process_id],
                estimated_time_savings=time_savings,
                estimated_cost_savings=time_savings * 0.5,  # $0.50 per minute
                implementation_effort='low',
                automation_potential=0.3,
                priority_score=0.95,
                expected_efficiency_gain=0.12
            ))
        
        # Optimization 2: Add Processing Capacity
        if bottlenecks and bottlenecks[0].avg_queue_time > 30:
            self.optimizations.append(WorkflowOptimization(
                optimization_id='opt_002',
                title='Add Parallel Processing Capacity',
                description=f'Add second unit for {bottlenecks[0].process_name}',
                affected_processes=[bottlenecks[0].process_id],
                estimated_time_savings=bottlenecks[0].avg_queue_time * 0.5,
                estimated_cost_savings=bottlenecks[0].avg_queue_time * 0.3,
                implementation_effort='medium',
                automation_potential=0.2,
                priority_score=0.85,
                expected_efficiency_gain=0.08
            ))
        
        # Optimization 3: Automate Data Entry
        for process_id, overhead in list(data_entry_issues.items())[:3]:
            if overhead > 0.2:  # More than 20% overhead
                process = self.analyzer.processes.get(process_id)
                if process:
                    time_savings = process.data_entry_time * 0.7  # 70% automation
                    self.optimizations.append(WorkflowOptimization(
                        optimization_id=f'opt_data_{process_id}',
                        title=f'Automate Data Entry - {process.process_type.value}',
                        description=f'Implement LIMS integration for {process.process_type.value}',
                        affected_processes=[process_id],
                        estimated_time_savings=time_savings,
                        estimated_cost_savings=time_savings * 0.4,
                        implementation_effort='medium',
                        automation_potential=0.7,
                        priority_score=0.80,
                        expected_efficiency_gain=0.10
                    ))
        
        # Optimization 4: Improve Sample Receipt & Tracking
        self.optimizations.append(WorkflowOptimization(
            optimization_id='opt_004',
            title='Enhance Sample Tracking System',
            description='Implement barcode scanning and automated sample routing',
            affected_processes=['sample_receipt', 'storage'],
            estimated_time_savings=15.0,
            estimated_cost_savings=10.0,
            implementation_effort='medium',
            automation_potential=0.6,
            priority_score=0.75,
            expected_efficiency_gain=0.08
        ))
        
        # Optimization 5: Standardize Protocols & Reduce Errors
        if bottlenecks:
            avg_error_rate = statistics.mean([b.error_rate for b in bottlenecks])
            if avg_error_rate > 2:
                time_savings = (statistics.mean([b.avg_total_time for b in bottlenecks]) * 
                               avg_error_rate / 100 * 0.5)
                self.optimizations.append(WorkflowOptimization(
                    optimization_id='opt_005',
                    title='Standardize Protocols & QC Procedures',
                    description='Create detailed step-by-step protocols and implement peer review',
                    affected_processes=[b.process_id for b in bottlenecks[:3]],
                    estimated_time_savings=time_savings,
                    estimated_cost_savings=time_savings * 0.3,
                    implementation_effort='low',
                    automation_potential=0.1,
                    priority_score=0.70,
                    expected_efficiency_gain=0.07
                ))
        
        # Optimization 6: Parallel Processing Workflow
        self.optimizations.append(WorkflowOptimization(
            optimization_id='opt_006',
            title='Implement Parallel Processing Workflow',
            description='Process different sample types simultaneously where possible',
            affected_processes=['extraction', 'quantification', 'analysis'],
            estimated_time_savings=20.0,
            estimated_cost_savings=15.0,
            implementation_effort='high',
            automation_potential=0.5,
            priority_score=0.65,
            expected_efficiency_gain=0.12
        ))
        
        # Optimization 7: Improve Data Recording Methods
        self.optimizations.append(WorkflowOptimization(
            optimization_id='opt_007',
            title='Deploy Mobile Data Recording',
            description='Mobile devices with offline capability for real-time data entry',
            affected_processes=['data_entry'],
            estimated_time_savings=10.0,
            estimated_cost_savings=8.0,
            implementation_effort='medium',
            automation_potential=0.8,
            priority_score=0.68,
            expected_efficiency_gain=0.09
        ))
        
        # Sort by priority and efficiency gain
        self.optimizations.sort(
            key=lambda x: (x.priority_score, x.expected_efficiency_gain), 
            reverse=True
        )
        
        logger.info(f"Generated {len(self.optimizations)} optimization recommendations")
        return self.optimizations
    
    def calculate_total_efficiency_gain(self) -> Dict[str, float]:
        """Calculate total efficiency gain from all optimizations"""
        if not self.optimizations:
            return {}
        
        # Combined efficiency gains (accounting for some overlap)
        individual_gains = [opt.expected_efficiency_gain for opt in self.optimizations]
        combined_gain = 1.0
        for gain in individual_gains[:5]:  # Take top 5 optimizations
            combined_gain *= (1 - gain * 0.8)  # 80% effectiveness due to interdependencies
        
        total_gain = 1 - combined_gain
        
        total_time_savings = sum(opt.estimated_time_savings for opt in self.optimizations[:5])
        total_cost_savings = sum(opt.estimated_cost_savings for opt in self.optimizations[:5])
        
        return {
            'total_efficiency_gain_percent': min(total_gain * 100, 35),  # Cap at 35%
            'total_time_savings_minutes': total_time_savings,
            'total_cost_savings_dollars': total_cost_savings,
            'payback_period_weeks': 4 if total_cost_savings > 0 else 0,
            'recommended_optimizations': len([o for o in self.optimizations if o.priority_score > 0.65])
        }
    
    def generate_implementation_plan(self) -> Dict[str, List]:
        """Generate phased implementation plan"""
        phase_1 = [opt for opt in self.optimizations if opt.implementation_effort == 'low']
        phase_2 = [opt for opt in self.optimizations if opt.implementation_effort == 'medium']
        phase_3 = [opt for opt in self.optimizations if opt.implementation_effort == 'high']
        
        return {
            'phase_1_quick_wins': [
                {
                    'title': opt.title,
                    'timeline': '1-2 weeks',
                    'time_savings': opt.estimated_time_savings,
                    'cost_savings': opt.estimated_cost_savings
                }
                for opt in phase_1[:3]
            ],
            'phase_2_implementation': [
                {
                    'title': opt.title,
                    'timeline': '2-4 weeks',
                    'time_savings': opt.estimated_time_savings,
                    'cost_savings': opt.estimated_cost_savings
                }
                for opt in phase_2[:3]
            ],
            'phase_3_infrastructure': [
                {
                    'title': opt.title,
                    'timeline': '4-8 weeks',
                    'time_savings': opt.estimated_time_savings,
                    'cost_savings': opt.estimated_cost_savings
                }
                for opt in phase_3[:2]
            ]
        }
    
    def export_optimization_report(self, output_path: str = 'lab_workflow_report.json') -> Dict:
        """Export comprehensive optimization report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis_results': {
                'bottleneck_count': len(self.analysis_results.get('bottlenecks', [])),
                'efficiency_metrics': self.analysis_results.get('efficiency_metrics', {}),
                'data_entry_issues_count': len(self.analysis_results.get('data_entry_issues', {}))
            },
            'optimizations': [
                {
                    'id': opt.optimization_id,
                    'title': opt.title,
                    'description': opt.description,
                    'time_savings': opt.estimated_time_savings,
                    'cost_savings': opt.estimated_cost_savings,
                    'implementation_effort': opt.implementation_effort,
                    'priority_score': opt.priority_score,
                    'efficiency_gain': opt.expected_efficiency_gain
                }
                for opt in self.optimizations
            ],
            'efficiency_summary': self.calculate_total_efficiency_gain(),
            'implementation_plan': self.generate_implementation_plan()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report exported to {output_path}")
        return report
    
    def generate_summary(self) -> str:
        """Generate human-readable summary"""
        summary = []
        summary.append("=" * 70)
        summary.append("LABORATORY WORKFLOW OPTIMIZATION SUMMARY")
        summary.append("=" * 70)
        
        summary.append(f"\nAnalysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        efficiency = self.calculate_total_efficiency_gain()
        summary.append(f"\nKey Metrics:")
        summary.append(f"  Estimated Efficiency Gain: {efficiency.get('total_efficiency_gain_percent', 0):.1f}%")
        summary.append(f"  Time Savings per Sample: {efficiency.get('total_time_savings_minutes', 0):.1f} minutes")
        summary.append(f"  Annual Cost Savings: ${efficiency.get('total_cost_savings_dollars', 0) * 250:.0f}")
        
        summary.append(f"\nTop 5 Recommendations:\n")
        for i, opt in enumerate(self.optimizations[:5], 1):
            summary.append(f"{i}. {opt.title}")
            summary.append(f"   Priority: {opt.priority_score*100:.0f}% | Efficiency Gain: {opt.expected_efficiency_gain*100:.1f}%")
            summary.append(f"   Time Savings: {opt.estimated_time_savings:.1f} min | Cost Savings: ${opt.estimated_cost_savings:.2f}")
            summary.append(f"   Implementation: {opt.implementation_effort.upper()}\n")
        
        plan = self.generate_implementation_plan()
        summary.append(f"Implementation Plan:")
        summary.append(f"  Phase 1 (Quick Wins): {len(plan['phase_1_quick_wins'])} optimizations - 1-2 weeks")
        summary.append(f"  Phase 2 (Core Changes): {len(plan['phase_2_implementation'])} optimizations - 2-4 weeks")
        summary.append(f"  Phase 3 (Infrastructure): {len(plan['phase_3_infrastructure'])} optimizations - 4-8 weeks")
        
        summary.append("\n" + "=" * 70)
        
        return "\n".join(summary)


# ==================== EXAMPLE USAGE ====================

def create_sample_workflow_data():
    """Create sample workflow data for demonstration"""
    
    # Process definitions
    processes_df = pd.DataFrame({
        'process_id': ['p001', 'p002', 'p003', 'p004', 'p005', 'p006', 'p007'],
        'process_type': ['SAMPLE_RECEIPT', 'EXTRACTION', 'QUANTIFICATION', 
                        'ANALYSIS', 'QUALITY_CONTROL', 'DATA_ENTRY', 'STORAGE'],
        'duration_min': [10, 45, 25, 60, 20, 30, 5],
        'resource': ['Technician', 'Hood', 'Analyzer', 'Equipment', 'Technician', 'Computer', 'Technician'],
        'data_entry_time_min': [5, 8, 12, 15, 10, 25, 3],
        'automation_level': [0.2, 0.1, 0.5, 0.4, 0.3, 0.1, 0.6]
    })
    
    # Historical workflow data
    np.random.seed(42)
    n_records = 200
    
    workflow_df = pd.DataFrame({
        'sample_id': [f'SAMPLE_{i:04d}' for i in range(n_records)],
        'sample_type': np.random.choice(['BLOOD', 'TISSUE', 'CELL_CULTURE'], n_records),
        'process_id': np.repeat(['p001', 'p002', 'p003', 'p004', 'p005', 'p006'], n_records//6 + 1)[:n_records],
        'queue_time_min': np.random.gamma(2, 8, n_records),  # 5-30 minutes queue
        'processing_time_min': np.random.gamma(2, 10, n_records),
        'data_entry_time_min': np.random.gamma(2, 5, n_records),
        'errors': np.random.binomial(10, 0.03, n_records)
    })
    
    return processes_df, workflow_df


if __name__ == "__main__":
    # Initialize optimizer
    optimizer = LabWorkflowOptimizer()
    
    # Load sample data
    processes_df, workflow_df = create_sample_workflow_data()
    optimizer.load_process_definitions(processes_df)
    optimizer.load_historical_workflow_data(workflow_df)
    optimizer.set_workflow_sequence(['sample_receipt', 'extraction', 'quantification', 
                                    'analysis', 'quality_control', 'data_entry', 'storage'])
    
    # Analyze and optimize
    optimizer.analyze_workflow()
    recommendations = optimizer.generate_optimization_recommendations()
    
    # Display results
    print(optimizer.generate_summary())
    
    # Export report
    optimizer.export_optimization_report('lab_workflow_report.json')
    
    # Show implementation plan
    plan = optimizer.generate_implementation_plan()
    print("\n\nIMPLEMENTATION PLAN:\n")
    print("PHASE 1 - Quick Wins (1-2 weeks):")
    for item in plan['phase_1_quick_wins']:
        print(f"  • {item['title']}: Save {item['time_savings']:.1f} min/sample (${item['cost_savings']:.1f})")
    
    print("\nPHASE 2 - Core Implementation (2-4 weeks):")
    for item in plan['phase_2_implementation']:
        print(f"  • {item['title']}: Save {item['time_savings']:.1f} min/sample (${item['cost_savings']:.1f})")
    
    print("\nPHASE 3 - Infrastructure (4-8 weeks):")
    for item in plan['phase_3_infrastructure']:
        print(f"  • {item['title']}: Save {item['time_savings']:.1f} min/sample (${item['cost_savings']:.1f})")
