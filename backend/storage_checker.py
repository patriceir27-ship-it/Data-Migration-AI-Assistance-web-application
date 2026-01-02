import psutil
import os
import json
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class StorageChecker:
    def __init__(self):
        self.threshold_warning = 0.85  # 85% usage threshold for warning
        self.threshold_critical = 0.95  # 95% usage threshold for critical
    
    def check_capacity(self, device_info: Dict, required_size: int = 0) -> Dict:
        """Check storage capacity for a device"""
        device_type = device_info.get('type', 'unknown')
        path = device_info.get('path', '/')
        
        try:
            if device_type == 'local':
                # Check local storage
                usage = psutil.disk_usage(path)
            elif device_type in ['phone', 'external']:
                # For external devices, simulate or use specific checks
                usage = self._simulate_external_storage(device_info)
            elif device_type == 'database':
                # For databases, check database storage
                usage = self._check_database_storage(device_info)
            else:
                # Default to local storage
                usage = psutil.disk_usage('/')
            
            # Calculate available space
            total = usage.total
            used = usage.used
            free = usage.free
            percent_used = usage.percent / 100
            
            # Check if required size fits
            fits = free >= required_size
            
            # Calculate safety margin (keep at least 10% free)
            safety_margin = total * 0.1
            fits_with_margin = free - required_size >= safety_margin
            
            # Determine status
            if percent_used >= self.threshold_critical:
                status = 'critical'
            elif percent_used >= self.threshold_warning:
                status = 'warning'
            elif not fits:
                status = 'insufficient'
            elif not fits_with_margin:
                status = 'marginal'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'total_bytes': total,
                'total_human': self._human_readable_size(total),
                'used_bytes': used,
                'used_human': self._human_readable_size(used),
                'free_bytes': free,
                'free_human': self._human_readable_size(free),
                'percent_used': percent_used,
                'fits': fits,
                'fits_with_margin': fits_with_margin,
                'required_bytes': required_size,
                'required_human': self._human_readable_size(required_size),
                'available_after_migration': free - required_size,
                'available_after_human': self._human_readable_size(free - required_size)
            }
            
        except Exception as e:
            logger.error(f"Storage check failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'fits': False,
                'fits_with_margin': False
            }
    
    def _simulate_external_storage(self, device_info: Dict) -> Any:
        """Simulate external storage check"""
        # In production, implement actual device detection
        # For simulation, return realistic values
        class Usage:
            def __init__(self):
                # Simulate 128GB device with 35% used
                self.total = 128 * 1024 * 1024 * 1024
                self.used = self.total * 0.35
                self.free = self.total - self.used
                self.percent = 35.0
        
        return Usage()
    
    def _check_database_storage(self, device_info: Dict) -> Any:
        """Check database storage"""
        # In production, connect to database and check storage
        # For simulation, return realistic values
        class Usage:
            def __init__(self):
                # Simulate 500GB database with 42% used
                self.total = 500 * 1024 * 1024 * 1024
                self.used = self.total * 0.42
                self.free = self.total - self.used
                self.percent = 42.0
        
        return Usage()
    
    def compare_storage(self, source_info: Dict, dest_info: Dict, data_size: int) -> Dict:
        """Compare storage between source and destination"""
        source_check = self.check_capacity(source_info, 0)  # Don't check required size for source
        dest_check = self.check_capacity(dest_info, data_size)
        
        comparison = {
            'source': source_check,
            'destination': dest_check,
            'can_migrate': dest_check.get('fits', False),
            'can_migrate_safely': dest_check.get('fits_with_margin', False),
            'size_difference': dest_check.get('free_bytes', 0) - data_size,
            'size_difference_human': self._human_readable_size(
                dest_check.get('free_bytes', 0) - data_size
            )
        }
        
        # Add warnings if needed
        warnings = []
        if not comparison['can_migrate']:
            warnings.append("Destination has insufficient space for migration")
        elif not comparison['can_migrate_safely']:
            warnings.append("Destination will have less than 10% free space after migration")
        
        if source_check.get('status') == 'critical':
            warnings.append("Source storage is critically full")
        
        comparison['warnings'] = warnings
        
        return comparison
    
    def get_recommendations(self, source_check: Dict, dest_check: Dict, compatibility: Dict) -> List[str]:
        """Get storage recommendations"""
        recommendations = []
        
        # Source recommendations
        if source_check.get('status') == 'critical':
            recommendations.append("Source storage is critically full. Consider cleaning up before migration")
        elif source_check.get('status') == 'warning':
            recommendations.append("Source storage is getting full. Monitor usage during migration")
        
        # Destination recommendations
        if not dest_check.get('fits', False):
            recommendations.append("Destination has insufficient space. Free up space or choose another destination")
        elif not dest_check.get('fits_with_margin', False):
            recommendations.append("Destination will have limited space after migration. Consider cleaning up destination first")
        
        if dest_check.get('status') == 'critical':
            recommendations.append("Destination storage is critically full. Not recommended for migration")
        elif dest_check.get('status') == 'warning':
            recommendations.append("Destination storage is getting full. Consider alternative storage")
        
        # Compatibility-based recommendations
        if not compatibility.get('compatible', False):
            recommendations.append("Compatibility issues detected. Consider data conversion before migration")
        
        # General recommendations
        recommendations.append("Always verify data integrity after migration")
        recommendations.append("Keep backups of important data before migration")
        
        return recommendations
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        if size_bytes < 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def get_system_storage(self) -> Dict:
        """Get system storage information"""
        partitions = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'total_human': self._human_readable_size(usage.total),
                    'used': usage.used,
                    'used_human': self._human_readable_size(usage.used),
                    'free': usage.free,
                    'free_human': self._human_readable_size(usage.free),
                    'percent': usage.percent
                })
            except Exception as e:
                logger.error(f"Failed to get partition info for {partition.mountpoint}: {str(e)}")
        
        # Calculate totals
        total_space = sum(p['total'] for p in partitions)
        total_used = sum(p['used'] for p in partitions)
        total_free = sum(p['free'] for p in partitions)
        
        return {
            'partitions': partitions,
            'total': {
                'total': total_space,
                'total_human': self._human_readable_size(total_space),
                'used': total_used,
                'used_human': self._human_readable_size(total_used),
                'free': total_free,
                'free_human': self._human_readable_size(total_free),
                'percent': (total_used / total_space * 100) if total_space > 0 else 0
            }
        }
