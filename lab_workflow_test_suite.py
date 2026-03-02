"""
Laboratory Workflow Optimizer - Test Suite & Validation
Tests core functionality and validates optimization accuracy
"""

import numpy as np
import pandas as pd
from lab_workflow_optimizer import (
    LabWorkflowOptimizer,
    LabProcess,
    LabWorkflowAnalyzer,
    SampleProcessingOptimizer,
    DataRecordingOptimizer,
    ProcessType,
    SampleType
)


class LWOTestSuite:
    """Comprehensive test suite for Lab Workflow Optimizer"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*70)
        print("LABORATORY WORKFLOW OPTIMIZER - TEST SUITE")
        print("="*70 + "\n")
        
        # Data loading tests
        self.test_process_definition_loading()
        self.test_workflow_data_loading()
        self.test_workflow_sequence()
        
        # Analysis tests
        self.test_bottleneck_identification()
        self.test_efficiency_metrics()
        self.test_data_entry_analysis()
        
        # Optimization tests
        self.test_batch_processing_optimization()
        self.test_queue_reduction()
        self.test_automation_savings()
        
        # Integration tests
        self.test_optimization_recommendation_generation()
        self.test_implementation_plan_generation()
        self.test_total_efficiency_calculation()
        
        # Output tests
        self.test_report_generation()
        self.test_summary_generation()
        
        # Validation tests
        self.test_efficiency_gain_reasonable()
        
        # Print summary
        self.print_test_summary()
    
    def test_process_definition_loading(self):
        """Test loading process definitions"""
        test_name = "Process Definition Loading"
        try:
            optimizer = LabWorkflowOptimizer()
            
            processes_df = pd.DataFrame({
                'process_id': ['p1', 'p2', 'p3'],
                'process_type': ['SAMPLE_RECEIPT', 'EXTRACTION', 'ANALYSIS'],
                'duration_min': [10, 45, 60],
                'resource': ['Technician', 'Hood', 'Equipment'],
                'data_entry_time_min': [5, 8, 12],
                'automation_level': [0.2, 0.1, 0.4]
            })
            
            optimizer.load_process_definitions(processes_df)
            
            assert len(optimizer.analyzer.processes) == 3
            assert 'p1' in optimizer.analyzer.processes
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_workflow_data_loading(self):
        """Test loading workflow execution data"""
        test_name = "Workflow Data Loading"
        try:
            optimizer = LabWorkflowOptimizer()
            
            np.random.seed(42)
            workflow_df = pd.DataFrame({
                'sample_id': [f'S{i}' for i in range(100)],
                'sample_type': ['BLOOD'] * 100,
                'process_id': np.repeat(['p1', 'p2', 'p3'], 34)[:100],
                'queue_time_min': np.random.uniform(5, 30, 100),
                'processing_time_min': np.random.uniform(10, 60, 100),
                'data_entry_time_min': np.random.uniform(2, 20, 100),
                'errors': np.random.binomial(5, 0.02, 100)
            })
            
            optimizer.analyzer.load_historical_data(workflow_df)
            
            assert len(optimizer.analyzer.process_times) > 0
            assert len(optimizer.analyzer.queue_times) > 0
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_workflow_sequence(self):
        """Test workflow sequence definition"""
        test_name = "Workflow Sequence"
        try:
            optimizer = LabWorkflowOptimizer()
            sequence = ['receipt', 'processing', 'qc', 'storage']
            
            optimizer.set_workflow_sequence(sequence)
            
            assert optimizer.analyzer.workflow_sequence == sequence
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_bottleneck_identification(self):
        """Test identification of workflow bottlenecks"""
        test_name = "Bottleneck Identification"
        try:
            optimizer = LabWorkflowOptimizer()
            
            # Create process with known bottleneck
            process1 = LabProcess(
                process_id='p1',
                process_type=ProcessType.SAMPLE_RECEIPT,
                duration_minutes=10,
                resource_required='Technician',
                queue_time_minutes=5,
                data_entry_time=2
            )
            
            # Process with high queue time
            process2 = LabProcess(
                process_id='p2',
                process_type=ProcessType.EXTRACTION,
                duration_minutes=45,
                resource_required='Hood',
                queue_time_minutes=45,  # Long queue
                error_rate=5.0,
                data_entry_time=8
            )
            
            optimizer.analyzer.add_process(process1)
            optimizer.analyzer.add_process(process2)
            
            # Add some workflow data
            np.random.seed(42)
            workflow_df = pd.DataFrame({
                'sample_id': [f'S{i}' for i in range(100)],
                'sample_type': ['BLOOD'] * 100,
                'process_id': np.repeat(['p1', 'p2'], 50),
                'queue_time_min': [5]*50 + [45]*50,
                'processing_time_min': [10]*50 + [45]*50,
                'data_entry_time_min': [2]*50 + [8]*50,
                'errors': [0]*50 + [5]*50
            })
            
            optimizer.analyzer.load_historical_data(workflow_df)
            bottlenecks = optimizer.analyzer.identify_bottlenecks()
            
            assert len(bottlenecks) > 0
            # p2 should be identified as worse bottleneck
            assert bottlenecks[0].process_id == 'p2'
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_efficiency_metrics(self):
        """Test workflow efficiency metric calculation"""
        test_name = "Efficiency Metrics"
        try:
            optimizer = LabWorkflowOptimizer()
            
            np.random.seed(42)
            workflow_df = pd.DataFrame({
                'sample_id': [f'S{i}' for i in range(100)],
                'sample_type': ['BLOOD'] * 100,
                'process_id': np.repeat(['p1', 'p2'], 50),
                'queue_time_min': [10]*50 + [20]*50,
                'processing_time_min': [30]*50 + [40]*50,
                'data_entry_time_min': [5]*50 + [10]*50,
                'errors': [1]*50 + [2]*50
            })
            
            optimizer.analyzer.load_historical_data(workflow_df)
            metrics = optimizer.analyzer.calculate_workflow_efficiency()
            
            assert 'processing_efficiency' in metrics
            assert 'queue_percentage' in metrics
            assert metrics['processing_efficiency'] > 0
            assert metrics['queue_percentage'] >= 0
            assert metrics['queue_percentage'] <= 100
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_data_entry_analysis(self):
        """Test data entry bottleneck identification"""
        test_name = "Data Entry Analysis"
        try:
            processes = {
                'p1': LabProcess('p1', ProcessType.SAMPLE_RECEIPT, 10, 'Tech', 
                                data_entry_time=1),
                'p2': LabProcess('p2', ProcessType.DATA_ENTRY, 5, 'Computer', 
                                data_entry_time=25),  # High data entry
                'p3': LabProcess('p3', ProcessType.STORAGE, 5, 'Tech', 
                                data_entry_time=2)
            }
            
            bottlenecks = DataRecordingOptimizer.identify_data_entry_bottlenecks(processes)
            
            assert len(bottlenecks) > 0
            assert 'p2' in bottlenecks
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_batch_processing_optimization(self):
        """Test batch processing efficiency calculation"""
        test_name = "Batch Processing Optimization"
        try:
            # Test efficiency gain from batching
            efficiency = SampleProcessingOptimizer.calculate_batch_efficiency(
                batch_size=10,
                setup_time=5,
                unit_process_time=5
            )
            
            # Should show improvement with batching
            assert efficiency > 0.8  # At least 80% efficiency
            
            # Larger batch should be more efficient
            efficiency_large = SampleProcessingOptimizer.calculate_batch_efficiency(
                batch_size=20,
                setup_time=5,
                unit_process_time=5
            )
            assert efficiency_large > efficiency
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_queue_reduction(self):
        """Test queue time reduction from added capacity"""
        test_name = "Queue Reduction"
        try:
            process_times = [20] * 50  # 50 samples at 20 min each
            
            result = SampleProcessingOptimizer.reduce_queue_time(
                process_times,
                additional_capacity=1
            )
            
            assert 'capacity_increase_percent' in result
            assert 'throughput_improvement' in result
            assert 'queue_reduction_estimate' in result
            assert result['capacity_increase_percent'] > 0
            assert result['throughput_improvement'] > 0
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_automation_savings(self):
        """Test automation time savings calculation"""
        test_name = "Automation Savings"
        try:
            data_entry_time = 20  # 20 minutes of data entry
            
            result = DataRecordingOptimizer.automation_time_savings(
                data_entry_time,
                automation_level=0.7
            )
            
            assert result['current_time'] == data_entry_time
            assert result['automated_time'] == 14  # 20 * 0.7
            assert result['time_savings_percent'] == 70
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_optimization_recommendation_generation(self):
        """Test optimization recommendation generation"""
        test_name = "Optimization Recommendation Generation"
        try:
            optimizer = LabWorkflowOptimizer()
            
            processes_df = pd.DataFrame({
                'process_id': ['p1', 'p2', 'p3'],
                'process_type': ['SAMPLE_RECEIPT', 'EXTRACTION', 'ANALYSIS'],
                'duration_min': [10, 45, 60],
                'resource': ['Technician', 'Hood', 'Equipment'],
                'data_entry_time_min': [5, 8, 30],  # High for p3
                'automation_level': [0.2, 0.1, 0.1]
            })
            
            np.random.seed(42)
            workflow_df = pd.DataFrame({
                'sample_id': [f'S{i}' for i in range(100)],
                'sample_type': ['BLOOD'] * 100,
                'process_id': np.repeat(['p1', 'p2', 'p3'], 34)[:100],
                'queue_time_min': np.random.uniform(5, 50, 100),
                'processing_time_min': np.random.uniform(10, 70, 100),
                'data_entry_time_min': [5]*34 + [8]*33 + [30]*33,
                'errors': np.random.binomial(5, 0.03, 100)
            })
            
            optimizer.load_process_definitions(processes_df)
            optimizer.load_historical_workflow_data(workflow_df)
            optimizer.analyze_workflow()
            
            recommendations = optimizer.generate_optimization_recommendations()
            
            assert len(recommendations) > 0
            assert all(hasattr(r, 'title') for r in recommendations)
            assert all(hasattr(r, 'estimated_time_savings') for r in recommendations)
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_implementation_plan_generation(self):
        """Test implementation plan generation"""
        test_name = "Implementation Plan Generation"
        try:
            optimizer = LabWorkflowOptimizer()
            
            processes_df = pd.DataFrame({
                'process_id': ['p1', 'p2'],
                'process_type': ['SAMPLE_RECEIPT', 'EXTRACTION'],
                'duration_min': [10, 45],
                'resource': ['Technician', 'Hood'],
                'data_entry_time_min': [5, 8],
                'automation_level': [0.2, 0.1]
            })
            
            workflow_df = pd.DataFrame({
                'sample_id': ['S1', 'S2'],
                'sample_type': ['BLOOD', 'BLOOD'],
                'process_id': ['p1', 'p2'],
                'queue_time_min': [10, 30],
                'processing_time_min': [10, 45],
                'data_entry_time_min': [5, 8],
                'errors': [1, 2]
            })
            
            optimizer.load_process_definitions(processes_df)
            optimizer.load_historical_workflow_data(workflow_df)
            optimizer.analyze_workflow()
            optimizer.generate_optimization_recommendations()
            
            plan = optimizer.generate_implementation_plan()
            
            assert 'phase_1_quick_wins' in plan
            assert 'phase_2_implementation' in plan
            assert 'phase_3_infrastructure' in plan
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_total_efficiency_calculation(self):
        """Test total efficiency gain calculation"""
        test_name = "Total Efficiency Calculation"
        try:
            optimizer = LabWorkflowOptimizer()
            
            processes_df = pd.DataFrame({
                'process_id': ['p1', 'p2', 'p3'],
                'process_type': ['SAMPLE_RECEIPT', 'EXTRACTION', 'ANALYSIS'],
                'duration_min': [10, 45, 60],
                'resource': ['Technician', 'Hood', 'Equipment'],
                'data_entry_time_min': [5, 8, 15],
                'automation_level': [0.2, 0.1, 0.3]
            })
            
            workflow_df = pd.DataFrame({
                'sample_id': [f'S{i}' for i in range(100)],
                'sample_type': ['BLOOD'] * 100,
                'process_id': np.repeat(['p1', 'p2', 'p3'], 34)[:100],
                'queue_time_min': np.random.uniform(5, 30, 100),
                'processing_time_min': np.random.uniform(10, 70, 100),
                'data_entry_time_min': np.random.uniform(2, 20, 100),
                'errors': np.random.binomial(5, 0.02, 100)
            })
            
            optimizer.load_process_definitions(processes_df)
            optimizer.load_historical_workflow_data(workflow_df)
            optimizer.analyze_workflow()
            optimizer.generate_optimization_recommendations()
            
            efficiency = optimizer.calculate_total_efficiency_gain()
            
            assert 'total_efficiency_gain_percent' in efficiency
            assert efficiency['total_efficiency_gain_percent'] > 0
            assert efficiency['total_efficiency_gain_percent'] <= 35
            assert 'total_time_savings_minutes' in efficiency
            assert 'total_cost_savings_dollars' in efficiency
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_report_generation(self):
        """Test JSON report export"""
        test_name = "Report Generation"
        try:
            optimizer = LabWorkflowOptimizer()
            
            processes_df = pd.DataFrame({
                'process_id': ['p1', 'p2'],
                'process_type': ['SAMPLE_RECEIPT', 'EXTRACTION'],
                'duration_min': [10, 45],
                'resource': ['Tech', 'Hood'],
                'data_entry_time_min': [5, 8],
                'automation_level': [0.2, 0.1]
            })
            
            workflow_df = pd.DataFrame({
                'sample_id': ['S1', 'S2'],
                'sample_type': ['BLOOD', 'BLOOD'],
                'process_id': ['p1', 'p2'],
                'queue_time_min': [10, 30],
                'processing_time_min': [10, 45],
                'data_entry_time_min': [5, 8],
                'errors': [1, 2]
            })
            
            optimizer.load_process_definitions(processes_df)
            optimizer.load_historical_workflow_data(workflow_df)
            optimizer.analyze_workflow()
            optimizer.generate_optimization_recommendations()
            
            report = optimizer.export_optimization_report('/tmp/test_workflow_report.json')
            
            assert 'timestamp' in report
            assert 'analysis_results' in report
            assert 'optimizations' in report
            assert 'efficiency_summary' in report
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_summary_generation(self):
        """Test human-readable summary generation"""
        test_name = "Summary Generation"
        try:
            optimizer = LabWorkflowOptimizer()
            
            processes_df = pd.DataFrame({
                'process_id': ['p1', 'p2'],
                'process_type': ['SAMPLE_RECEIPT', 'EXTRACTION'],
                'duration_min': [10, 45],
                'resource': ['Tech', 'Hood'],
                'data_entry_time_min': [5, 8],
                'automation_level': [0.2, 0.1]
            })
            
            workflow_df = pd.DataFrame({
                'sample_id': ['S1', 'S2'],
                'sample_type': ['BLOOD', 'BLOOD'],
                'process_id': ['p1', 'p2'],
                'queue_time_min': [10, 30],
                'processing_time_min': [10, 45],
                'data_entry_time_min': [5, 8],
                'errors': [1, 2]
            })
            
            optimizer.load_process_definitions(processes_df)
            optimizer.load_historical_workflow_data(workflow_df)
            optimizer.analyze_workflow()
            optimizer.generate_optimization_recommendations()
            
            summary = optimizer.generate_summary()
            
            assert isinstance(summary, str)
            assert 'LABORATORY WORKFLOW OPTIMIZATION' in summary
            assert 'Efficiency Gain' in summary
            
            self._pass(test_name)
        except Exception as e:
            self._fail(test_name, str(e))
    
    def test_efficiency_gain_reasonable(self):
        """Test that efficiency gains are reasonable (20-35%)"""
        test_name = "Efficiency Gain Reasonableness"
        try:
            optimizer = LabWorkflowOptimizer()
            
            processes_df = pd.DataFrame({
                'process_id': [f'p{i}' for i in range(7)],
                'process_type': ['SAMPLE_RECEIPT', 'EXTRACTION', 'EXTRACTION',
                                'QUANTIFICATION', 'ANALYSIS', 'QUALITY_CONTROL', 'DATA_ENTRY'],
                'duration_min': [10, 45, 25, 20, 60, 20, 30],
                'resource': ['Tech', 'Hood', 'Hood', 'Instrument', 'Equipment', 'Tech', 'Computer'],
                'data_entry_time_min': [5, 8, 5, 8, 15, 10, 25],
                'automation_level': [0.2, 0.1, 0.1, 0.5, 0.4, 0.3, 0.1]
            })
            
            np.random.seed(42)
            workflow_df = pd.DataFrame({
                'sample_id': [f'S{i}' for i in range(300)],
                'sample_type': np.random.choice(['BLOOD', 'TISSUE'], 300),
                'process_id': np.repeat([f'p{i}' for i in range(7)], 43)[:300],
                'queue_time_min': np.random.gamma(2, 8, 300),
                'processing_time_min': np.random.gamma(2, 15, 300),
                'data_entry_time_min': np.random.gamma(2, 8, 300),
                'errors': np.random.binomial(10, 0.03, 300)
            })
            
            optimizer.load_process_definitions(processes_df)
            optimizer.load_historical_workflow_data(workflow_df)
            optimizer.analyze_workflow()
            optimizer.generate_optimization_recommendations()
            
            efficiency = optimizer.calculate_total_efficiency_gain()
            gain = efficiency.get('total_efficiency_gain_percent', 0)
            
            # Efficiency should be reasonable
            assert 15 < gain < 35, f"Efficiency gain {gain}% is outside expected range (15-35%)"
            
            self._pass(test_name, f"Gain = {gain:.1f}%")
        except Exception as e:
            self._fail(test_name, str(e))
    
    def _pass(self, test_name, message=""):
        """Record passing test"""
        self.tests_passed += 1
        msg = f"✓ PASS: {test_name}"
        if message:
            msg += f" ({message})"
        self.test_results.append(msg)
        print(msg)
    
    def _fail(self, test_name, error_msg=""):
        """Record failing test"""
        self.tests_failed += 1
        msg = f"✗ FAIL: {test_name}"
        if error_msg:
            msg += f" - {error_msg}"
        self.test_results.append(msg)
        print(msg)
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"\nTotal Tests: {self.tests_passed + self.tests_failed}")
        print(f"Passed: {self.tests_passed} ✓")
        print(f"Failed: {self.tests_failed} ✗")
        
        pass_rate = (self.tests_passed / (self.tests_passed + self.tests_failed)) * 100
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.tests_failed} test(s) failed")
        
        print("="*70 + "\n")


if __name__ == "__main__":
    suite = LWOTestSuite()
    suite.run_all_tests()
