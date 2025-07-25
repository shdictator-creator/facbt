"""
FACBT Engine - Main engine for Facebook account creation bot
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from managers.proxy_manager import ProxyManager
from managers.user_agent_manager import UserAgentManager
from managers.email_manager import EmailManager
from managers.identity_manager import IdentityManager
from managers.session_manager import SessionManager
from simulation.human_behavior import HumanBehaviorSimulator
from simulation.anti_detection import AntiDetectionSystem
from utils.logger import LoggerFactory


class EngineStatus(Enum):
    """Engine status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class AccountResult:
    """Result of account creation attempt"""
    success: bool
    account_id: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    error: Optional[str] = None
    creation_time: Optional[float] = None
    proxy_used: Optional[str] = None
    user_agent_used: Optional[str] = None


@dataclass
class EngineStatistics:
    """Engine performance statistics"""
    total_attempts: int = 0
    successful_creations: int = 0
    failed_creations: int = 0
    average_creation_time: float = 0.0
    success_rate: float = 0.0
    uptime: float = 0.0
    accounts_per_hour: float = 0.0


class FACBTEngine:
    """Main engine for Facebook account creation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = LoggerFactory.create_logger(__name__)
        self.status = EngineStatus.STOPPED
        self.start_time: Optional[float] = None
        
        # Statistics
        self.statistics = EngineStatistics()
        self.creation_times: List[float] = []
        
        # Managers
        self.proxy_manager: Optional[ProxyManager] = None
        self.user_agent_manager: Optional[UserAgentManager] = None
        self.email_manager: Optional[EmailManager] = None
        self.identity_manager: Optional[IdentityManager] = None
        self.session_manager: Optional[SessionManager] = None
        
        # Services
        self.behavior_simulator: Optional[HumanBehaviorSimulator] = None
        self.anti_detection: Optional[AntiDetectionSystem] = None
        
        # Control
        self.shutdown_event = asyncio.Event()
        
    async def initialize(self):
        """Initialize all engine components"""
        try:
            self.logger.info("Initializing FACBT Engine...")
            self.status = EngineStatus.STARTING
            
            # Initialize managers
            await self._initialize_managers()
            
            # Initialize services
            await self._initialize_services()
            
            # Run health checks
            await self._run_health_checks()
            
            self.status = EngineStatus.RUNNING
            self.start_time = time.time()
            self.logger.info("FACBT Engine initialized successfully")
            
        except Exception as e:
            self.status = EngineStatus.ERROR
            self.logger.error(f"Failed to initialize engine: {e}")
            raise
            
    async def _initialize_managers(self):
        """Initialize all manager components"""
        self.logger.info("Initializing managers...")
        
        # Proxy Manager
        proxy_config = self.config.get('proxy', {})
        self.proxy_manager = ProxyManager(proxy_config)
        await self.proxy_manager.initialize()
        
        # User Agent Manager
        ua_config = self.config.get('user_agent', {})
        self.user_agent_manager = UserAgentManager(ua_config)
        await self.user_agent_manager.initialize()
        
        # Email Manager
        email_config = self.config.get('email', {})
        self.email_manager = EmailManager(email_config)
        await self.email_manager.initialize()
        
        # Identity Manager
        identity_config = self.config.get('identity', {})
        self.identity_manager = IdentityManager(identity_config)
        
        # Session Manager
        session_config = self.config.get('session', {})
        self.session_manager = SessionManager(session_config)
        
        self.logger.info("All managers initialized successfully")
        
    async def _initialize_services(self):
        """Initialize all service components"""
        self.logger.info("Initializing services...")
        
        # Behavior Simulator
        behavior_config = self.config.get('behavior', {})
        self.behavior_simulator = HumanBehaviorSimulator(behavior_config)
        
        # Anti-Detection System
        detection_config = self.config.get('anti_detection', {})
        self.anti_detection = AntiDetectionSystem(detection_config)
        await self.anti_detection.initialize()
        
        self.logger.info("All services initialized successfully")
        
    async def _run_health_checks(self):
        """Run health checks on all components"""
        self.logger.info("Running health checks...")
        
        health_checks = [
            ("Proxy Manager", self.proxy_manager.health_check()),
            ("User Agent Manager", self.user_agent_manager.health_check()),
            ("Email Manager", self.email_manager.health_check()),
            ("Identity Manager", self.identity_manager.health_check()),
            ("Behavior Simulator", self.behavior_simulator.health_check()),
            ("Anti-Detection System", self.anti_detection.health_check())
        ]
        
        for name, check in health_checks:
            try:
                result = await check
                if result:
                    self.logger.info(f"✅ {name} health check passed")
                else:
                    self.logger.warning(f"⚠️ {name} health check failed")
            except Exception as e:
                self.logger.error(f"❌ {name} health check error: {e}")
                
    async def start(self):
        """Start the engine"""
        try:
            self.logger.info("Starting FACBT Engine...")
            self.status = EngineStatus.RUNNING
            self.start_time = time.time()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.logger.info("FACBT Engine started successfully")
            
        except Exception as e:
            self.status = EngineStatus.ERROR
            self.logger.error(f"Failed to start engine: {e}")
            raise
            
    async def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks"""
        # Start resource monitoring
        asyncio.create_task(self._monitor_resources())
        
        # Start statistics updates
        asyncio.create_task(self._update_statistics())
        
        # Start health monitoring
        asyncio.create_task(self._monitor_health())
        
    async def create_account(self) -> AccountResult:
        """Create a single Facebook account"""
        start_time = time.time()
        self.statistics.total_attempts += 1
        
        try:
            self.logger.info("Starting account creation process...")
            
            # Generate identity
            identity = await self.identity_manager.generate_identity()
            self.logger.info(f"Generated identity: {identity.first_name} {identity.last_name}")
            
            # Create email
            email = await self.email_manager.create_email()
            self.logger.info(f"Created temporary email: {email.address}")
            
            # Get proxy
            proxy = await self.proxy_manager.get_proxy()
            self.logger.info(f"Selected proxy: {proxy.host}:{proxy.port}")
            
            # Get user agent
            user_agent = await self.user_agent_manager.get_user_agent()
            self.logger.info(f"Selected user agent: {user_agent.browser} {user_agent.version}")
            
            # Create session
            session = await self.session_manager.create_session(
                proxy=proxy,
                user_agent=user_agent
            )
            
            # Initialize state machine
            state_machine = AccountCreationStateMachine(
                identity=identity,
                email=email,
                session=session,
                facebook_service=self.facebook_service,
                behavior_simulator=self.behavior_simulator
            )
            
            # Execute account creation workflow
            result = await state_machine.execute()
            
            if result.success:
                self.statistics.successful_creations += 1
                creation_time = time.time() - start_time
                self.creation_times.append(creation_time)
                
                self.logger.info(f"Account created successfully in {creation_time:.2f}s")
                
                return AccountResult(
                    success=True,
                    account_id=result.account_id,
                    email=email.address,
                    password=identity.password,
                    creation_time=creation_time,
                    proxy_used=f"{proxy.host}:{proxy.port}",
                    user_agent_used=str(user_agent)
                )
            else:
                self.statistics.failed_creations += 1
                self.logger.error(f"Account creation failed: {result.error}")
                
                return AccountResult(
                    success=False,
                    error=result.error,
                    creation_time=time.time() - start_time
                )
                
        except Exception as e:
            self.statistics.failed_creations += 1
            error_msg = f"Account creation error: {e}"
            self.logger.error(error_msg)
            
            return AccountResult(
                success=False,
                error=error_msg,
                creation_time=time.time() - start_time
            )
        finally:
            # Cleanup resources
            try:
                if 'session' in locals():
                    await self.session_manager.cleanup_session(session)
                if 'proxy' in locals():
                    await self.proxy_manager.release_proxy(proxy)
                if 'email' in locals():
                    await self.email_manager.cleanup_email(email)
            except Exception as e:
                self.logger.warning(f"Cleanup error: {e}")
                
    async def stop(self):
        """Stop the engine gracefully"""
        try:
            self.logger.info("Stopping FACBT Engine...")
            self.status = EngineStatus.STOPPING
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Stop all managers and services
            if self.facebook_service:
                await self.facebook_service.stop()
            if self.session_manager:
                await self.session_manager.stop()
            if self.email_manager:
                await self.email_manager.stop()
            if self.proxy_manager:
                await self.proxy_manager.stop()
                
            # Stop thread manager
            if self.thread_manager:
                await self.thread_manager.stop()
                
            self.status = EngineStatus.STOPPED
            self.logger.info("FACBT Engine stopped successfully")
            
        except Exception as e:
            self.status = EngineStatus.ERROR
            self.logger.error(f"Error stopping engine: {e}")
            
    async def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "status": self.status.value,
            "uptime": uptime,
            "statistics": {
                "total_attempts": self.statistics.total_attempts,
                "successful_creations": self.statistics.successful_creations,
                "failed_creations": self.statistics.failed_creations,
                "success_rate": self._calculate_success_rate(),
                "average_creation_time": self._calculate_average_creation_time(),
                "accounts_per_hour": self._calculate_accounts_per_hour()
            },
            "resources": {
                "proxy_pool_size": await self.proxy_manager.get_pool_size() if self.proxy_manager else 0,
                "active_sessions": await self.session_manager.get_active_count() if self.session_manager else 0,
                "email_services_status": await self.email_manager.get_services_status() if self.email_manager else {}
            }
        }
        
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.statistics.total_attempts == 0:
            return 0.0
        return (self.statistics.successful_creations / self.statistics.total_attempts) * 100
        
    def _calculate_average_creation_time(self) -> float:
        """Calculate average account creation time"""
        if not self.creation_times:
            return 0.0
        return sum(self.creation_times) / len(self.creation_times)
        
    def _calculate_accounts_per_hour(self) -> float:
        """Calculate accounts created per hour"""
        if not self.start_time or self.statistics.successful_creations == 0:
            return 0.0
        uptime_hours = (time.time() - self.start_time) / 3600
        return self.statistics.successful_creations / uptime_hours
        
    async def _monitor_resources(self):
        """Monitor system resources"""
        while not self.shutdown_event.is_set():
            try:
                # Monitor memory usage
                import psutil
                memory_percent = psutil.virtual_memory().percent
                cpu_percent = psutil.cpu_percent()
                
                if memory_percent > 80:
                    self.logger.warning(f"High memory usage: {memory_percent}%")
                if cpu_percent > 90:
                    self.logger.warning(f"High CPU usage: {cpu_percent}%")
                    
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)
                
    async def _update_statistics(self):
        """Update statistics periodically"""
        while not self.shutdown_event.is_set():
            try:
                # Update calculated statistics
                self.statistics.success_rate = self._calculate_success_rate()
                self.statistics.average_creation_time = self._calculate_average_creation_time()
                self.statistics.accounts_per_hour = self._calculate_accounts_per_hour()
                
                if self.start_time:
                    self.statistics.uptime = time.time() - self.start_time
                    
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Statistics update error: {e}")
                await asyncio.sleep(60)
                
    async def _monitor_health(self):
        """Monitor component health"""
        while not self.shutdown_event.is_set():
            try:
                await self._run_health_checks()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(600)

