"""
GC Content Calculator
A Python program to calculate the GC content (percentage of G and C bases) 
in genetic sequences.
"""

from typing import Tuple, List, Dict, Optional
import re


class GCContentCalculator:
    """Calculate GC content for DNA/RNA sequences"""
    
    def __init__(self, sequence: str, sequence_type: str = "DNA"):
        """
        Initialize with a genetic sequence
        
        Args:
            sequence: DNA or RNA sequence string
            sequence_type: "DNA" or "RNA"
        """
        self.original_sequence = sequence
        self.sequence_type = sequence_type.upper()
        self.sequence = self.normalize_sequence(sequence)
        self.is_valid = self.validate_sequence()
    
    def normalize_sequence(self, seq: str) -> str:
        """
        Normalize sequence by converting to uppercase and removing whitespace
        
        Args:
            seq: Raw sequence string
            
        Returns:
            Normalized sequence
        """
        # Remove whitespace and convert to uppercase
        normalized = seq.upper().replace(' ', '').replace('\n', '').replace('\t', '')
        return normalized
    
    def validate_sequence(self) -> bool:
        """
        Validate that sequence contains only valid bases
        
        Returns:
            True if valid, False otherwise
        """
        if not self.sequence:
            return False
        
        if self.sequence_type == "DNA":
            valid_bases = set('ATGCN')
        elif self.sequence_type == "RNA":
            valid_bases = set('AUGCN')
        else:
            return False
        
        # Check if all characters are valid
        return all(base in valid_bases for base in self.sequence)
    
    def calculate_gc_content(self) -> Optional[float]:
        """
        Calculate GC content as percentage
        
        Returns:
            GC content percentage (0-100), or None if invalid
        """
        if not self.is_valid:
            return None
        
        if len(self.sequence) == 0:
            return None
        
        # Count G and C bases (case-insensitive)
        gc_count = self.sequence.count('G') + self.sequence.count('C')
        
        # Calculate percentage
        gc_percentage = (gc_count / len(self.sequence)) * 100
        
        return gc_percentage
    
    def get_base_composition(self) -> Dict[str, Tuple[int, float]]:
        """
        Get count and percentage of all bases
        
        Returns:
            Dictionary with base: (count, percentage)
        """
        if not self.is_valid:
            return {}
        
        if len(self.sequence) == 0:
            return {}
        
        composition = {}
        
        if self.sequence_type == "DNA":
            bases = ['A', 'T', 'G', 'C', 'N']
        else:
            bases = ['A', 'U', 'G', 'C', 'N']
        
        for base in bases:
            count = self.sequence.count(base)
            percentage = (count / len(self.sequence)) * 100 if len(self.sequence) > 0 else 0
            composition[base] = (count, percentage)
        
        return composition
    
    def calculate_gc_by_region(self, window_size: int) -> List[Tuple[int, int, float]]:
        """
        Calculate GC content in sliding windows
        
        Args:
            window_size: Size of window in bases
            
        Returns:
            List of (start_pos, end_pos, gc_content) tuples
        """
        if not self.is_valid or window_size <= 0 or window_size > len(self.sequence):
            return []
        
        regions = []
        
        for i in range(len(self.sequence) - window_size + 1):
            region = self.sequence[i:i+window_size]
            gc_count = region.count('G') + region.count('C')
            gc_percentage = (gc_count / window_size) * 100
            regions.append((i, i + window_size, gc_percentage))
        
        return regions
    
    def find_cg_islands(self, island_length: int = 300, gc_threshold: float = 50.0) -> List[Tuple[int, int, float]]:
        """
        Find CpG islands (regions with high GC content)
        
        Args:
            island_length: Minimum length for CpG island
            gc_threshold: Minimum GC% to qualify as island
            
        Returns:
            List of (start_pos, end_pos, gc_content) for islands
        """
        if not self.is_valid:
            return []
        
        islands = []
        regions = self.calculate_gc_by_region(island_length)
        
        for start, end, gc_content in regions:
            if gc_content >= gc_threshold:
                islands.append((start, end, gc_content))
        
        # Merge overlapping islands
        if islands:
            islands = self.merge_overlapping_regions(islands)
        
        return islands
    
    @staticmethod
    def merge_overlapping_regions(regions: List[Tuple[int, int, float]]) -> List[Tuple[int, int, float]]:
        """
        Merge overlapping regions
        
        Args:
            regions: List of (start, end, value) tuples
            
        Returns:
            Merged list of regions
        """
        if not regions:
            return []
        
        # Sort by start position
        sorted_regions = sorted(regions, key=lambda x: x[0])
        
        merged = [list(sorted_regions[0])]
        
        for current in sorted_regions[1:]:
            last = merged[-1]
            # If regions overlap, merge them
            if current[0] <= last[1]:
                merged[-1] = (last[0], max(last[1], current[1]), (last[2] + current[2]) / 2)
            else:
                merged.append(list(current))
        
        return [tuple(region) for region in merged]
    
    def calculate_skew(self) -> Tuple[float, float]:
        """
        Calculate GC and AT skew
        
        GC skew = (G - C) / (G + C)
        AT skew = (A - T) / (A + T)
        
        Returns:
            (gc_skew, at_skew) tuple
        """
        if not self.is_valid:
            return None, None
        
        g_count = self.sequence.count('G')
        c_count = self.sequence.count('C')
        a_count = self.sequence.count('A')
        t_count = self.sequence.count('T')
        
        # GC skew
        gc_total = g_count + c_count
        gc_skew = (g_count - c_count) / gc_total if gc_total > 0 else 0
        
        # AT skew
        at_total = a_count + t_count
        at_skew = (a_count - t_count) / at_total if at_total > 0 else 0
        
        return gc_skew, at_skew
    
    def print_analysis(self):
        """Print comprehensive GC content analysis"""
        print(f"\n{'='*70}")
        print(f"GC CONTENT ANALYSIS")
        print(f"{'='*70}\n")
        
        if not self.is_valid:
            print(f"❌ ERROR: Invalid sequence for {self.sequence_type}")
            print(f"   Valid bases for {self.sequence_type}: ", end="")
            print("ATGCN" if self.sequence_type == "DNA" else "AUGCN")
            print()
            return
        
        # Basic information
        print(f"{'SEQUENCE INFORMATION':-^70}")
        print(f"  Sequence Type: {self.sequence_type}")
        print(f"  Sequence Length: {len(self.sequence)} bp")
        print(f"  Display: {self.sequence[:80]}{'...' if len(self.sequence) > 80 else ''}")
        print()
        
        # GC Content
        print(f"{'GC CONTENT ANALYSIS':-^70}")
        gc_content = self.calculate_gc_content()
        print(f"  GC Content: {gc_content:.2f}%")
        print()
        
        # Base Composition
        print(f"{'BASE COMPOSITION':-^70}")
        composition = self.get_base_composition()
        for base, (count, percentage) in composition.items():
            if count > 0 or base in ['G', 'C']:
                bar_length = int(percentage / 2)
                bar = '█' * bar_length
                print(f"  {base}: {count:5d} ({percentage:6.2f}%) {bar}")
        print()
        
        # Skew Analysis
        print(f"{'SKEW ANALYSIS':-^70}")
        gc_skew, at_skew = self.calculate_skew()
        print(f"  GC Skew: {gc_skew:.4f}")
        print(f"    (Positive = more G, Negative = more C)")
        print(f"  AT Skew: {at_skew:.4f}")
        print(f"    (Positive = more A, Negative = more T)")
        print()
        
        print(f"{'='*70}\n")


def analyze_from_string(sequence: str, sequence_type: str = "DNA"):
    """
    Analyze GC content from a string sequence
    
    Args:
        sequence: DNA/RNA sequence string
        sequence_type: "DNA" or "RNA"
    """
    calculator = GCContentCalculator(sequence, sequence_type)
    calculator.print_analysis()
    
    if calculator.is_valid:
        return calculator.calculate_gc_content()
    return None


def analyze_from_file(filepath: str, sequence_type: str = "DNA") -> Optional[float]:
    """
    Analyze GC content from a FASTA file
    
    Args:
        filepath: Path to FASTA file
        sequence_type: "DNA" or "RNA"
        
    Returns:
        GC content percentage
    """
    try:
        with open(filepath, 'r') as f:
            sequence = ""
            for line in f:
                line = line.strip()
                # Skip FASTA header lines
                if not line.startswith('>'):
                    sequence += line
        
        calculator = GCContentCalculator(sequence, sequence_type)
        calculator.print_analysis()
        
        if calculator.is_valid:
            return calculator.calculate_gc_content()
        return None
    
    except FileNotFoundError:
        print(f"❌ Error: File '{filepath}' not found")
        return None
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None


def main():
    """Main function with example usage"""
    
    print(f"\n{'='*70}")
    print("GC CONTENT CALCULATOR")
    print(f"{'='*70}\n")
    
    # Example 1: Simple sequence
    print("Example 1: Simple DNA Sequence")
    print("-" * 70)
    seq1 = "ATGCGATCGATCGTAGC"
    gc1 = analyze_from_string(seq1, "DNA")
    
    # Example 2: Longer sequence with multiple features
    print("\nExample 2: Longer DNA Sequence")
    print("-" * 70)
    seq2 = """
    ATGCGATCGATCGTAGCTAGCTAGCTAGC
    ATGCGATCGATCGTAGCTAGCTAGCTAGC
    ATGCGATCGATCGTAGCTAGCTAGCTAGC
    GCTAGCTAGCTAGCTAGCTAGCTAGCTA
    """
    gc2 = analyze_from_string(seq2, "DNA")
    
    # Example 3: Sequence with high GC content
    print("\nExample 3: High GC Content Sequence")
    print("-" * 70)
    seq3 = "GCGCGCGCGCGCGCGC" * 5
    gc3 = analyze_from_string(seq3, "DNA")
    
    # Example 4: Sequence with low GC content
    print("\nExample 4: Low GC Content Sequence (High AT)")
    print("-" * 70)
    seq4 = "ATATATATAT" * 10
    gc4 = analyze_from_string(seq4, "DNA")
    
    # Example 5: CpG Island detection
    print("\nExample 5: CpG Island Detection")
    print("-" * 70)
    
    # Create a sequence with a CpG island
    background = "ATATATAT" * 50  # Low GC background
    island = "GCGCGCGC" * 50      # High GC island
    combined = background + island + background
    
    calculator = GCContentCalculator(combined, "DNA")
    calculator.print_analysis()
    
    print(f"{'CpG ISLAND ANALYSIS':-^70}")
    islands = calculator.find_cg_islands(island_length=300, gc_threshold=50.0)
    
    if islands:
        print(f"  Found {len(islands)} CpG island(s):")
        for i, (start, end, gc_content) in enumerate(islands, 1):
            length = end - start
            print(f"    Island {i}: Position {start}-{end} (Length: {length} bp, GC: {gc_content:.2f}%)")
    else:
        print("  No CpG islands found above threshold")
    print()
    
    # Example 6: Windowed GC content analysis
    print("\nExample 6: Windowed GC Content Analysis")
    print("-" * 70)
    
    test_seq = "GCGCGCGCATATATAT" * 3
    calculator = GCContentCalculator(test_seq, "DNA")
    
    print(f"  Sequence: {test_seq}")
    print(f"  Total GC Content: {calculator.calculate_gc_content():.2f}%")
    print(f"\n  Window-based GC content (window size = 8 bp):")
    
    regions = calculator.calculate_gc_by_region(window_size=8)
    for i, (start, end, gc_content) in enumerate(regions[:8], 1):
        window_seq = test_seq[start:end]
        print(f"    Window {i} ({start}-{end}): {window_seq} → {gc_content:.2f}%")
    
    if len(regions) > 8:
        print(f"    ... and {len(regions) - 8} more windows")
    print()
    
    # Example 7: RNA sequence
    print("\nExample 7: RNA Sequence Analysis")
    print("-" * 70)
    rna_seq = "AUGCGAUCGAUCGUAGC"
    gc_rna = analyze_from_string(rna_seq, "RNA")
    
    # Example 8: Invalid sequence handling
    print("\nExample 8: Invalid Sequence Handling")
    print("-" * 70)
    invalid_seq = "ATGCXYZ"
    calculator = GCContentCalculator(invalid_seq, "DNA")
    calculator.print_analysis()
    print()
    
    print(f"{'='*70}")
    print("Analysis Complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
