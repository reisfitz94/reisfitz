"""
Genetic Sequence Analyzer
A Python program to analyze three genetic sequences simultaneously.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from collections import Counter
import re


# Genetic code translation table (codon to amino acid)
GENETIC_CODE = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'
}

# Complement base mapping
COMPLEMENT = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}


@dataclass
class GeneticSequence:
    """Represents a genetic sequence with metadata"""
    name: str
    sequence: str
    sequence_type: str = "DNA"  # DNA or RNA
    
    def __post_init__(self):
        # Normalize to uppercase
        self.sequence = self.sequence.upper()
        
        # Validate sequence
        valid_chars = set('ATGCN') if self.sequence_type == "DNA" else set('AUGCN')
        if not all(c in valid_chars for c in self.sequence):
            raise ValueError(f"Invalid characters in sequence. Valid: {valid_chars}")
    
    def get_length(self) -> int:
        """Get sequence length"""
        return len(self.sequence)
    
    def get_complement(self) -> str:
        """Get the complement strand"""
        return ''.join(COMPLEMENT.get(base, 'N') for base in self.sequence)
    
    def get_reverse_complement(self) -> str:
        """Get the reverse complement strand"""
        return self.get_complement()[::-1]
    
    def __str__(self) -> str:
        return f"{self.name}: {self.sequence[:50]}{'...' if len(self.sequence) > 50 else ''}"


class SequenceAnalyzer:
    """Analyzes genetic sequences"""
    
    def __init__(self, seq1: GeneticSequence, seq2: GeneticSequence, seq3: GeneticSequence):
        """Initialize with three genetic sequences"""
        self.sequences = [seq1, seq2, seq3]
        self.results = {}
    
    def analyze_gc_content(self) -> Dict[str, float]:
        """Calculate GC content for each sequence"""
        gc_contents = {}
        
        for seq in self.sequences:
            gc_count = seq.sequence.count('G') + seq.sequence.count('C')
            gc_content = (gc_count / len(seq.sequence)) * 100 if len(seq.sequence) > 0 else 0
            gc_contents[seq.name] = gc_content
        
        return gc_contents
    
    def analyze_base_composition(self) -> Dict[str, Dict[str, float]]:
        """Calculate base composition percentages"""
        composition = {}
        
        for seq in self.sequences:
            length = len(seq.sequence)
            comp = {
                'A': (seq.sequence.count('A') / length) * 100,
                'T': (seq.sequence.count('T') / length) * 100,
                'G': (seq.sequence.count('G') / length) * 100,
                'C': (seq.sequence.count('C') / length) * 100,
            }
            composition[seq.name] = comp
        
        return composition
    
    def identify_start_codons(self) -> Dict[str, List[int]]:
        """Find start codon (ATG) positions"""
        start_codons = {}
        
        for seq in self.sequences:
            positions = []
            for i in range(len(seq.sequence) - 2):
                if seq.sequence[i:i+3] == 'ATG':
                    positions.append(i)
            start_codons[seq.name] = positions
        
        return start_codons
    
    def identify_stop_codons(self) -> Dict[str, List[int]]:
        """Find stop codons (TAA, TAG, TGA) positions"""
        stop_codons = {}
        stop_codon_set = {'TAA', 'TAG', 'TGA'}
        
        for seq in self.sequences:
            positions = []
            for i in range(len(seq.sequence) - 2):
                if seq.sequence[i:i+3] in stop_codon_set:
                    positions.append(i)
            stop_codons[seq.name] = positions
        
        return stop_codons
    
    def translate_to_protein(self, frame: int = 0) -> Dict[str, str]:
        """Translate DNA sequences to protein (amino acids)"""
        proteins = {}
        
        for seq in self.sequences:
            protein = ""
            for i in range(frame, len(seq.sequence) - 2, 3):
                codon = seq.sequence[i:i+3]
                if len(codon) == 3:
                    amino_acid = GENETIC_CODE.get(codon, 'X')  # X for unknown
                    protein += amino_acid
                    if amino_acid == '*':  # Stop codon
                        break
            proteins[seq.name] = protein
        
        return proteins
    
    def find_restriction_sites(self, restriction_site: str) -> Dict[str, List[int]]:
        """Find restriction enzyme cut sites"""
        sites = {}
        
        for seq in self.sequences:
            positions = []
            for i in range(len(seq.sequence) - len(restriction_site) + 1):
                if seq.sequence[i:i+len(restriction_site)] == restriction_site:
                    positions.append(i)
            sites[seq.name] = positions
        
        return sites
    
    def find_patterns(self, pattern: str) -> Dict[str, int]:
        """Find occurrences of a DNA pattern"""
        occurrences = {}
        
        for seq in self.sequences:
            count = len(re.findall(f'(?={pattern})', seq.sequence))
            occurrences[seq.name] = count
        
        return occurrences
    
    def hamming_distance(self, seq1_idx: int, seq2_idx: int) -> int:
        """Calculate Hamming distance between two sequences"""
        s1 = self.sequences[seq1_idx].sequence
        s2 = self.sequences[seq2_idx].sequence
        
        min_len = min(len(s1), len(s2))
        distance = sum(s1[i] != s2[i] for i in range(min_len))
        distance += abs(len(s1) - len(s2))
        
        return distance
    
    def calculate_pairwise_distances(self) -> Dict[Tuple[str, str], int]:
        """Calculate Hamming distances between all sequence pairs"""
        distances = {}
        
        for i in range(len(self.sequences)):
            for j in range(i + 1, len(self.sequences)):
                seq1_name = self.sequences[i].name
                seq2_name = self.sequences[j].name
                distance = self.hamming_distance(i, j)
                distances[(seq1_name, seq2_name)] = distance
        
        return distances
    
    def find_open_reading_frames(self) -> Dict[str, List[Tuple[int, int]]]:
        """Find Open Reading Frames (ORF) - sequences between start and stop codons"""
        orfs = {}
        
        for seq in self.sequences:
            seq_orfs = []
            start_positions = self.identify_start_codons()[seq.name]
            
            for start_pos in start_positions:
                for i in range(start_pos + 3, len(seq.sequence) - 2, 3):
                    if seq.sequence[i:i+3] in {'TAA', 'TAG', 'TGA'}:
                        seq_orfs.append((start_pos, i + 3))
                        break
            
            orfs[seq.name] = seq_orfs
        
        return orfs
    
    def codon_frequency(self) -> Dict[str, Dict[str, int]]:
        """Calculate codon frequencies"""
        codon_freqs = {}
        
        for seq in self.sequences:
            freq = Counter()
            for i in range(0, len(seq.sequence) - 2, 3):
                codon = seq.sequence[i:i+3]
                if len(codon) == 3:
                    freq[codon] += 1
            codon_freqs[seq.name] = dict(freq)
        
        return codon_freqs
    
    def print_comprehensive_analysis(self) -> None:
        """Print comprehensive analysis of all three sequences"""
        print(f"\n{'='*70}")
        print(f"GENETIC SEQUENCE ANALYSIS - THREE SEQUENCES")
        print(f"{'='*70}\n")
        
        # Sequence information
        print(f"{'SEQUENCE INFORMATION':-^70}")
        for seq in self.sequences:
            print(f"  Name: {seq.name}")
            print(f"  Length: {seq.get_length()} bp")
            print(f"  First 50 bp: {seq.sequence[:50]}")
            print()
        
        # GC Content
        print(f"{'GC CONTENT ANALYSIS':-^70}")
        gc_contents = self.analyze_gc_content()
        for name, gc in gc_contents.items():
            print(f"  {name}: {gc:.2f}%")
        print()
        
        # Base Composition
        print(f"{'BASE COMPOSITION (%)':-^70}")
        composition = self.analyze_base_composition()
        for name, comp in composition.items():
            print(f"  {name}:")
            for base, percent in comp.items():
                print(f"    {base}: {percent:.2f}%")
        print()
        
        # Start Codons
        print(f"{'START CODON (ATG) POSITIONS':-^70}")
        start_codons = self.identify_start_codons()
        for name, positions in start_codons.items():
            pos_str = ', '.join(map(str, positions)) if positions else "None found"
            print(f"  {name}: {pos_str}")
        print()
        
        # Stop Codons
        print(f"{'STOP CODON POSITIONS':-^70}")
        stop_codons = self.identify_stop_codons()
        for name, positions in stop_codons.items():
            pos_str = ', '.join(map(str, positions[:5])) if positions else "None found"
            if len(positions) > 5:
                pos_str += f" ... ({len(positions)} total)"
            print(f"  {name}: {pos_str}")
        print()
        
        # Protein Translation
        print(f"{'PROTEIN TRANSLATION (Reading Frame 0)':-^70}")
        proteins = self.translate_to_protein()
        for name, protein in proteins.items():
            display_protein = protein[:60] + ('...' if len(protein) > 60 else '')
            print(f"  {name}: {display_protein}")
        print()
        
        # Pairwise Distances
        print(f"{'PAIRWISE HAMMING DISTANCES':-^70}")
        distances = self.calculate_pairwise_distances()
        for (name1, name2), distance in distances.items():
            print(f"  {name1} vs {name2}: {distance} differences")
        print()
        
        # Open Reading Frames
        print(f"{'OPEN READING FRAMES (ORFs)':-^70}")
        orfs = self.find_open_reading_frames()
        for name, orf_list in orfs.items():
            if orf_list:
                print(f"  {name}: {len(orf_list)} ORF(s) found")
                for start, end in orf_list[:3]:
                    print(f"    Position {start}-{end} ({end-start} bp)")
            else:
                print(f"  {name}: No ORFs found")
        print()
        
        # Codon Frequency
        print(f"{'TOP 5 CODONS BY FREQUENCY':-^70}")
        codon_freqs = self.codon_frequency()
        for name, codons in codon_freqs.items():
            print(f"  {name}:")
            top_codons = sorted(codons.items(), key=lambda x: x[1], reverse=True)[:5]
            for codon, freq in top_codons:
                print(f"    {codon}: {freq} times")
        print()
        
        # Restriction sites
        print(f"{'RESTRICTION SITES (EcoRI: GAATTC)':-^70}")
        restriction_sites = self.find_restriction_sites('GAATTC')
        for name, positions in restriction_sites.items():
            pos_str = ', '.join(map(str, positions)) if positions else "None found"
            print(f"  {name}: {pos_str if len(pos_str) < 50 else pos_str[:47] + '...'}")
        print()
        
        print(f"{'='*70}\n")


def main():
    """Main function demonstrating genetic sequence analysis"""
    
    # Create three genetic sequences
    seq1 = GeneticSequence(
        name="Lambda Phage",
        sequence="ATGAGTGAGATGAGTGTGTCGCCCGATAGACGACAAACTGCTGCTGAAACAGCTGGAAGAAATG" +
                 "GAGAAGGCGATCCGTACCGCGGCAGAAAAAATGGATGATCTGGAAGCGCTGATGAAAGCGGCG" +
                 "CTGGAGATGCTGGAAGATCTGCTGAAACTGCTGCTGATGGATCGCTACCAGGAAGAAGATCTG" +
                 "ATGAAACGCCTGCTGGATACCGCGGTGAAACTGGAAATCGACCTGCTGATCGATCTGGAAGAA"
    )
    
    seq2 = GeneticSequence(
        name="T4 Bacteriophage",
        sequence="ATGAATGAAGATGAAGATGTCGCCCGATAGACGACAAACTGCTGCTGAAACAGCTGGAAGAAATG" +
                 "GAGAAGGCGATCCGTACCGCGGCAGAAAAAATGGATGATCTGGAAGCGCTGATGAAAGCGGCG" +
                 "CTGGAGATGCTGGAAGATCTGCTGAAACTGCTGCTGATGGATCGCTACCAGGAAGAAGATCTG" +
                 "ATGAAACGCCTGCTGGATACCGCGGTGAAACTGGAAATCGACCTGCTGATCGATCTGGAAGAA"
    )
    
    seq3 = GeneticSequence(
        name="Human Beta-Globin",
        sequence="ATGGCGTTCCACCAACCATCAGGCAGCTCCCACCCAGCACTGGAGGAAGAAGTCGACCCGCTGGA" +
                 "GGATCTGTCCACTCCTGATGAGCTGCACTGTGACGAAGACCAAGGCCTCACCGTGACGAAGAC" +
                 "CAAGGTCTCCTCCCCGCCGCCGGAGATCCTAGAACAACTGGAGACCCGGGATACATGACCACG" +
                 "CCGGCCGATCCCGGAAACACACACGGACACCGTCTCCTGCCGGCTGCGGCTGCGACGCGAGAC"
    )
    
    # Create analyzer
    analyzer = SequenceAnalyzer(seq1, seq2, seq3)
    
    # Perform comprehensive analysis
    analyzer.print_comprehensive_analysis()
    
    # Additional specific analyses
    print(f"{'='*70}")
    print(f"PATTERN SEARCH: Finding 'ATG' (Start Codon) Occurrences")
    print(f"{'='*70}\n")
    atg_pattern = analyzer.find_patterns('ATG')
    for name, count in atg_pattern.items():
        print(f"  {name}: {count} occurrences of ATG")
    print()
    
    # Restriction sites analysis
    print(f"{'='*70}")
    print(f"RESTRICTION ENZYME ANALYSIS")
    print(f"{'='*70}\n")
    
    restriction_enzymes = {
        'EcoRI (GAATTC)': 'GAATTC',
        'BamHI (GGATCC)': 'GGATCC',
        'HindIII (AAGCTT)': 'AAGCTT'
    }
    
    for enzyme_name, site in restriction_enzymes.items():
        sites = analyzer.find_restriction_sites(site)
        print(f"  {enzyme_name}:")
        for name, positions in sites.items():
            print(f"    {name}: {len(positions)} cut site(s)")
    print()


if __name__ == "__main__":
    main()
