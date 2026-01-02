import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class MigrationEngine:
    def __init__(self):
        self.supported_formats = {
            'databases': ['mysql', 'postgresql', 'mongodb', 'sqlite', 'oracle', 'sqlserver'],
            'devices': ['phone', 'computer', 'server', 'nas', 'cloud'],
            'file_types': ['*']  # All file types supported
        }
    
    def check_compatibility(self, source: Dict, destination: Dict) -> Dict:
        """Check compatibility between source and destination"""
        source_type = source.get('type')
        dest_type = destination.get('type')
        
        compatibility_score = 100  # Start with perfect score
        
        # Check if types are supported
        if source_type not in self.supported_formats['devices'] + self.supported_formats['databases']:
            compatibility_score -= 30
            
        if dest_type not in self.supported_formats['devices'] + self.supported_formats['databases']:
            compatibility_score -= 30
        
        # Database to database migration
        if source_type in self.supported_formats['databases'] and dest_type in self.supported_formats['databases']:
            if source_type != dest_type:
                compatibility_score -= 20  # Different database systems
        
        # Cross-platform considerations
        if source.get('os') and destination.get('os'):
            if source['os'] != destination['os']:
                compatibility_score -= 10
        
        # Connection protocol compatibility
        source_protocol = source.get('protocol', 'file')
        dest_protocol = destination.get('protocol', 'file')
        
        if source_protocol != dest_protocol:
            compatibility_score -= 15
        
        return {
            'compatible': compatibility_score >= 70,
            'score': compatibility_score,
            'issues': self._get_compatibility_issues(source, destination, compatibility_score),
            'recommendations': self._get_compatibility_recommendations(source, destination)
        }
    
    def _get_compatibility_issues(self, source: Dict, destination: Dict, score: int) -> List[str]:
        """Get list of compatibility issues"""
        issues = []
        
        if score < 100:
            issues.append("Partial compatibility detected")
        
        # Check for specific issues
        if source.get('type') == 'phone' and destination.get('type') == 'database':
            issues.append("Direct phone to database migration may require intermediate storage")
        
        if source.get('encryption') and not destination.get('supports_encryption'):
            issues.append("Source is encrypted but destination may not support encryption")
        
        return issues
    
    def _get_compatibility_recommendations(self, source: Dict, destination: Dict) -> List[str]:
        """Get recommendations for compatibility improvement"""
        recommendations = []
        
        # Add recommendations based on migration type
        if source.get('type') == 'database' and destination.get('type') == 'database':
            recommendations.append("Consider using database-native export/import tools for better performance")
            recommendations.append("Verify data types are compatible between database systems")
        
        elif source.get('type') in ['phone', 'computer'] and destination.get('type') == 'database':
            recommendations.append("Convert files to database-compatible format before migration")
            recommendations.append("Consider using CSV or JSON as intermediate format")
        
        # General recommendations
        recommendations.append("Perform a test migration with a small dataset first")
        recommendations.append("Verify network connectivity and bandwidth")
        
        return recommendations
    
    def analyze_files(self, files: List[Dict]) -> Dict:
        """Analyze files for migration optimization"""
        total_size = 0
        file_types = {}
        largest_file = {'name': '', 'size': 0}
        compressible_files = []
        
        for file_info in files:
            size = file_info.get('size', 0)
            total_size += size
            
            # Track file types
            filename = file_info.get('filename', '')
            if '.' in filename:
                ext = filename.split('.')[-1].lower()
                file_types[ext] = file_types.get(ext, 0) + size
            
            # Find largest file
            if size > largest_file['size']:
                largest_file = {'name': filename, 'size': size}
            
            # Check if file is compressible
            if self._is_compressible(filename):
                compressible_files.append(filename)
        
        # Calculate compression estimation
        estimated_compression = self._estimate_compression(file_types)
        
        return {
            'total_files': len(files),
            'total_size': total_size,
            'total_size_human': self._human_readable_size(total_size),
            'file_types': file_types,
            'largest_file': largest_file,
            'compressible_files': compressible_files,
            'estimated_compression_ratio': estimated_compression,
            'estimated_size_after_compression': total_size * (1 - estimated_compression),
            'recommended_batch_size': self._calculate_batch_size(total_size, len(files))
        }
    
    def _is_compressible(self, filename: str) -> bool:
        """Check if file type is compressible"""
        compressible_extensions = ['txt', 'csv', 'json', 'xml', 'log', 'html', 'css', 'js', 'doc', 'docx', 'pdf']
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            return ext in compressible_extensions
        return False
    
    def _estimate_compression(self, file_types: Dict) -> float:
        """Estimate compression ratio based on file types"""
        total_compressible = 0
        total_size = sum(file_types.values())
        
        compressible_types = ['txt', 'csv', 'json', 'xml', 'log', 'html', 'css', 'js']
        
        for ext, size in file_types.items():
            if ext in compressible_types:
                total_compressible += size
        
        if total_size == 0:
            return 0.0
        
        compressible_ratio = total_compressible / total_size
        
        # Estimate compression: 60% for compressible files, 10% for others
        return compressible_ratio * 0.6 + (1 - compressible_ratio) * 0.1
    
    def _calculate_batch_size(self, total_size: int, file_count: int) -> Dict:
        """Calculate optimal batch size for migration"""
        if total_size < 1024 * 1024 * 100:  # Less than 100MB
            return {'size': total_size, 'files': file_count, 'batches': 1}
        
        # Calculate based on size
        if total_size < 1024 * 1024 * 1024:  # Less than 1GB
            batch_size = 1024 * 1024 * 100  # 100MB batches
        elif total_size < 1024 * 1024 * 1024 * 10:  # Less than 10GB
            batch_size = 1024 * 1024 * 500  # 500MB batches
        else:
            batch_size = 1024 * 1024 * 1024  # 1GB batches
        
        batches = max(1, total_size // batch_size)
        files_per_batch = max(1, file_count // batches)
        
        return {
            'size_per_batch': batch_size,
            'files_per_batch': files_per_batch,
            'total_batches': batches,
            'recommended_parallel_transfers': min(5, batches)
        }
    
    def get_optimization_recommendations(self, analysis: Dict) -> List[str]:
        """Get optimization recommendations based on analysis"""
        recommendations = []
        
        total_size = analysis.get('total_size', 0)
        file_count = analysis.get('total_files', 0)
        compression_ratio = analysis.get('estimated_compression_ratio', 0)
        batch_info = analysis.get('recommended_batch_size', {})
        
        # Size-based recommendations
        if total_size > 1024 * 1024 * 1024 * 5:  # More than 5GB
            recommendations.append("Large dataset detected. Consider migrating during off-peak hours")
            recommendations.append("Enable compression to reduce transfer size")
        
        elif total_size < 1024 * 1024 * 10:  # Less than 10MB
            recommendations.append("Small dataset. Single transfer recommended for efficiency")
        
        # File count recommendations
        if file_count > 1000:
            recommendations.append(f"High file count ({file_count}). Consider archiving files before migration")
        
        # Compression recommendations
        if compression_ratio > 0.3:
            recommendations.append(f"High compression potential ({compression_ratio*100:.1f}%). Enable compression for faster transfer")
        
        # Batch recommendations
        if batch_info.get('total_batches', 1) > 1:
            recommendations.append(f"Split migration into {batch_info['total_batches']} batches for reliability")
            recommendations.append(f"Use {batch_info.get('recommended_parallel_transfers', 1)} parallel transfers for optimal speed")
        
        # General recommendations
        recommendations.append("Verify checksums after migration to ensure data integrity")
        recommendations.append("Keep source data until migration is verified complete")
        
        return recommendations
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def calculate_checksum(self, filepath: str) -> str:
        """Calculate MD5 checksum for a file"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def estimate_migration_time(self, total_size: int, connection_speed: float = 50) -> Dict:
        """Estimate migration time based on size and connection speed"""
        # connection_speed in MB/s
        if connection_speed <= 0:
            connection_speed = 1
        
        # Convert total_size to MB
        size_mb = total_size / (1024 * 1024)
        
        # Calculate time in seconds
        time_seconds = size_mb / connection_speed
        
        # Add overhead (20%)
        time_seconds *= 1.2
        
        # Convert to hours, minutes, seconds
        hours = int(time_seconds // 3600)
        minutes = int((time_seconds % 3600) // 60)
        seconds = int(time_seconds % 60)
        
        return {
            'total_seconds': time_seconds,
            'estimated_time': f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            'estimated_speed': f"{connection_speed} MB/s",
            'size_mb': size_mb
        }
