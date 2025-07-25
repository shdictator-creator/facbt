"""
Facebook Account Creator - Core account creation logic with human simulation
"""

import asyncio
import random
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from managers.proxy_manager import ProxyManager, Proxy
from managers.user_agent_manager import UserAgentManager, UserAgent
from managers.email_manager import EmailManager
from managers.identity_manager import IdentityManager, Identity
from simulation.human_behavior import HumanBehaviorSimulator
from simulation.anti_detection import AntiDetectionSystem
from utils.logger import LoggerFactory


class AccountStatus(Enum):
    """Account creation status"""
    PENDING = "pending"
    CREATING = "creating"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class AccountCreationResult:
    """Result of account creation attempt"""
    success: bool
    account_id: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    identity: Optional[Identity] = None
    status: AccountStatus = AccountStatus.PENDING
    error_message: Optional[str] = None
    creation_time: Optional[float] = None
    verification_required: bool = False
    verification_method: Optional[str] = None
    proxy_used: Optional[str] = None
    user_agent_used: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        if self.identity:
            result['identity'] = asdict(self.identity)
        result['status'] = self.status.value
        return result


class FacebookAccountCreator:
    """Creates Facebook accounts with human-like behavior"""
    
    def __init__(self, config: Dict[str, Any], 
                 proxy_manager: ProxyManager,
                 user_agent_manager: UserAgentManager,
                 email_manager: EmailManager,
                 identity_manager: IdentityManager,
                 behavior_simulator: HumanBehaviorSimulator,
                 anti_detection: AntiDetectionSystem):
        
        self.config = config
        self.proxy_manager = proxy_manager
        self.user_agent_manager = user_agent_manager
        self.email_manager = email_manager
        self.identity_manager = identity_manager
        self.behavior_simulator = behavior_simulator
        self.anti_detection = anti_detection
        
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Facebook configuration
        self.facebook_config = config.get('facebook', {})
        self.registration_url = self.facebook_config.get('registration_url', 'https://www.facebook.com/reg/')
        self.mobile_registration = self.facebook_config.get('mobile_registration', False)
        
        # Browser configuration
        self.browser_config = config.get('browser', {})
        self.headless = self.browser_config.get('headless', True)
        self.window_size = self.browser_config.get('window_size', (1366, 768))
        
        # Current session
        self.driver = None
        self.current_proxy = None
        self.current_user_agent = None
        self.session_start_time = None
        
    async def create_account(self, custom_identity: Optional[Identity] = None,
                           custom_email: Optional[str] = None) -> AccountCreationResult:
        """Create a Facebook account with human-like behavior"""
        
        self.session_start_time = time.time()
        result = AccountCreationResult(success=False, creation_time=self.session_start_time)
        
        try:
            self.logger.info("Starting Facebook account creation...")
            
            # Check rate limiting
            await self.anti_detection.wait_for_rate_limit()
            
            # Get resources
            identity = custom_identity or await self.identity_manager.generate_identity()
            email = custom_email or await self.email_manager.get_temporary_email()
            proxy = await self.proxy_manager.get_proxy()
            user_agent = await self.user_agent_manager.get_user_agent()
            
            if not email:
                raise Exception("Failed to get email address")
            if not proxy:
                self.logger.warning("No proxy available, proceeding without proxy")
            
            result.identity = identity
            result.email = email
            result.password = identity.password
            result.proxy_used = f"{proxy.host}:{proxy.port}" if proxy else None
            result.user_agent_used = user_agent.string
            
            self.logger.info(f"Creating account for {identity.first_name} {identity.last_name} ({email})")
            
            # Setup browser
            await self._setup_browser(proxy, user_agent)
            
            # Navigate to registration page
            await self._navigate_to_registration()
            
            # Fill registration form
            await self._fill_registration_form(identity, email)
            
            # Submit form
            await self._submit_registration_form()
            
            # Handle verification if required
            verification_result = await self._handle_verification(email)
            
            if verification_result['success']:
                result.success = True
                result.status = AccountStatus.COMPLETED
                result.account_id = verification_result.get('account_id')
                result.verification_required = verification_result.get('verification_required', False)
                result.verification_method = verification_result.get('verification_method')
                
                self.logger.info(f"Account created successfully: {email}")
            else:
                result.status = AccountStatus.FAILED
                result.error_message = verification_result.get('error')
                self.logger.error(f"Account creation failed: {result.error_message}")
                
        except Exception as e:
            result.status = AccountStatus.FAILED
            result.error_message = str(e)
            self.logger.error(f"Account creation failed: {e}")
            
            # Report proxy failure if applicable
            if self.current_proxy:
                await self.proxy_manager.report_proxy_failure(self.current_proxy)
                
        finally:
            # Cleanup
            await self._cleanup_browser()
            
            # Release resources
            if email and not result.success:
                await self.email_manager.release_email(email)
                
        return result
        
    async def _setup_browser(self, proxy: Optional[Proxy], user_agent: UserAgent):
        """Setup browser with stealth configuration"""
        try:
            # Chrome options
            chrome_options = Options()
            
            # Basic options
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument(f'--window-size={self.window_size[0]},{self.window_size[1]}')
            chrome_options.add_argument(f'--user-agent={user_agent.string}')
            
            # Stealth options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')  # We'll enable selectively
            
            # Proxy configuration
            if proxy:
                if proxy.protocol.value in ['http', 'https']:
                    chrome_options.add_argument(f'--proxy-server={proxy.url}')
                else:
                    # For SOCKS proxies, we need different configuration
                    chrome_options.add_argument(f'--proxy-server=socks5://{proxy.host}:{proxy.port}')
                    
            # Performance options for Termux
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=256')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            
            # Create driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.current_proxy = proxy
            self.current_user_agent = user_agent
            
            # Execute stealth scripts
            await self._execute_stealth_scripts()
            
            self.logger.debug("Browser setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser: {e}")
            raise
            
    async def _execute_stealth_scripts(self):
        """Execute JavaScript to make browser more human-like"""
        try:
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Override chrome property
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'chrome', {
                    get: () => ({
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    })
                });
            """)
            
            # Override plugins
            fingerprint = await self.anti_detection.bypass_javascript_detection()
            plugins_script = f"""
                Object.defineProperty(navigator, 'plugins', {{
                    get: () => {{
                        const plugins = [];
                        plugins.length = {len(fingerprint.get('plugins', []))};
                        return plugins;
                    }}
                }});
            """
            self.driver.execute_script(plugins_script)
            
            # Override permissions
            self.driver.execute_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            # Add mouse and keyboard event listeners
            self.driver.execute_script("""
                window.addEventListener('mousedown', function(e) {
                    window.mouseEvents = window.mouseEvents || [];
                    window.mouseEvents.push({type: 'mousedown', timestamp: Date.now()});
                });
                
                window.addEventListener('keydown', function(e) {
                    window.keyboardEvents = window.keyboardEvents || [];
                    window.keyboardEvents.push({type: 'keydown', timestamp: Date.now()});
                });
            """)
            
        except Exception as e:
            self.logger.warning(f"Failed to execute stealth scripts: {e}")
            
    async def _navigate_to_registration(self):
        """Navigate to Facebook registration page"""
        try:
            self.logger.info("Navigating to Facebook registration page...")
            
            # Add human delay before navigation
            delay = await self.anti_detection.inject_human_delays('page_load')
            await asyncio.sleep(delay)
            
            # Navigate to page
            self.driver.get(self.registration_url)
            
            # Wait for page load
            wait = WebDriverWait(self.driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Simulate reading the page
            reading_time = await self.behavior_simulator.simulate_reading(len(self.driver.page_source))
            await asyncio.sleep(min(reading_time, 10))  # Cap at 10 seconds
            
            # Check for honeypots
            honeypots = await self.anti_detection.detect_honeypots(self.driver.page_source)
            if honeypots:
                self.logger.warning(f"Detected honeypots on registration page: {honeypots}")
                
            self.logger.debug("Successfully navigated to registration page")
            
        except TimeoutException:
            raise Exception("Registration page failed to load")
        except Exception as e:
            raise Exception(f"Failed to navigate to registration page: {e}")
            
    async def _fill_registration_form(self, identity: Identity, email: str):
        """Fill the registration form with human-like behavior"""
        try:
            self.logger.info("Filling registration form...")
            
            # Define form fields in order
            form_fields = [
                {'id': 'firstname', 'value': identity.first_name, 'type': 'text'},
                {'id': 'lastname', 'value': identity.last_name, 'type': 'text'},
                {'id': 'reg_email__', 'value': email, 'type': 'email'},
                {'id': 'reg_email_confirmation__', 'value': email, 'type': 'email'},
                {'id': 'reg_passwd__', 'value': identity.password, 'type': 'password'}
            ]
            
            # Simulate form interaction
            form_actions = await self.behavior_simulator.simulate_form_interaction(form_fields)
            
            # Execute form filling actions
            for action in form_actions:
                await self._execute_form_action(action)
                
            # Fill birthday
            await self._fill_birthday(identity)
            
            # Select gender
            await self._select_gender(identity)
            
            self.logger.debug("Registration form filled successfully")
            
        except Exception as e:
            raise Exception(f"Failed to fill registration form: {e}")
            
    async def _execute_form_action(self, action: Dict[str, Any]):
        """Execute a form action with human behavior"""
        try:
            action_type = action['type']
            
            if action_type == 'delay':
                await asyncio.sleep(action['duration'])
                
            elif action_type == 'focus_field':
                field_id = action['field_id']
                element = self.driver.find_element(By.ID, field_id)
                
                # Simulate mouse movement to field
                location = element.location
                size = element.size
                target_pos = (
                    location['x'] + size['width'] // 2,
                    location['y'] + size['height'] // 2
                )
                
                # Move mouse and click
                await self._simulate_mouse_click(target_pos)
                element.click()
                
            elif action_type == 'type_char':
                char = action['char']
                element = self.driver.switch_to.active_element
                element.send_keys(char)
                
                # Add typing delay
                typing_delay = random.uniform(0.05, 0.2)
                await asyncio.sleep(typing_delay)
                
            elif action_type == 'backspace':
                element = self.driver.switch_to.active_element
                element.send_keys(Keys.BACKSPACE)
                
            elif action_type == 'key_press':
                key = action['key']
                element = self.driver.switch_to.active_element
                if key == 'Tab':
                    element.send_keys(Keys.TAB)
                elif key == 'Enter':
                    element.send_keys(Keys.ENTER)
                    
        except Exception as e:
            self.logger.warning(f"Failed to execute form action {action}: {e}")
            
    async def _simulate_mouse_click(self, position: Tuple[int, int]):
        """Simulate human-like mouse click"""
        try:
            # Get current mouse position (approximate)
            current_pos = (random.randint(0, self.window_size[0]), 
                          random.randint(0, self.window_size[1]))
            
            # Simulate mouse movement
            movement_actions = await self.behavior_simulator.simulate_mouse_movement(
                current_pos, position
            )
            
            # Execute movement (simplified for Selenium)
            for action in movement_actions[-3:]:  # Only last few movements
                await asyncio.sleep(0.01)
                
            # Simulate click
            click_actions = await self.behavior_simulator.simulate_click(position)
            
            # Add click delay
            for action in click_actions:
                if action['type'] in ['mouse_down', 'mouse_up']:
                    await asyncio.sleep(0.05)
                    
        except Exception as e:
            self.logger.debug(f"Mouse simulation error: {e}")
            
    async def _fill_birthday(self, identity: Identity):
        """Fill birthday fields"""
        try:
            # Birth month
            month_select = Select(self.driver.find_element(By.ID, "month"))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            month_select.select_by_value(str(identity.birth_date.month))
            
            # Birth day
            day_select = Select(self.driver.find_element(By.ID, "day"))
            await asyncio.sleep(random.uniform(0.3, 1.0))
            day_select.select_by_value(str(identity.birth_date.day))
            
            # Birth year
            year_select = Select(self.driver.find_element(By.ID, "year"))
            await asyncio.sleep(random.uniform(0.3, 1.0))
            year_select.select_by_value(str(identity.birth_date.year))
            
        except Exception as e:
            raise Exception(f"Failed to fill birthday: {e}")
            
    async def _select_gender(self, identity: Identity):
        """Select gender"""
        try:
            gender_value = "1" if identity.gender.lower() == "female" else "2"
            
            # Find gender radio button
            gender_element = self.driver.find_element(By.CSS_SELECTOR, f"input[value='{gender_value}']")
            
            # Simulate click
            await asyncio.sleep(random.uniform(0.5, 1.5))
            gender_element.click()
            
        except Exception as e:
            raise Exception(f"Failed to select gender: {e}")
            
    async def _submit_registration_form(self):
        """Submit the registration form"""
        try:
            self.logger.info("Submitting registration form...")
            
            # Find submit button
            submit_button = self.driver.find_element(By.NAME, "websubmit")
            
            # Pre-submission delay (user reviewing form)
            review_delay = random.uniform(2.0, 8.0)
            await asyncio.sleep(review_delay)
            
            # Simulate human errors occasionally
            if await self.anti_detection.simulate_human_errors('form_filling'):
                # Simulate going back to check a field
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
            # Click submit button
            submit_button.click()
            
            # Wait for response
            wait = WebDriverWait(self.driver, 30)
            
            # Check for various possible outcomes
            try:
                # Success - redirected to confirmation page
                wait.until(lambda driver: "facebook.com" in driver.current_url and "reg" not in driver.current_url)
                self.logger.info("Form submitted successfully")
                
            except TimeoutException:
                # Check for errors on the same page
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .errorMessage, [data-testid='error']")
                if error_elements:
                    error_text = error_elements[0].text
                    raise Exception(f"Registration error: {error_text}")
                else:
                    raise Exception("Form submission timeout - unknown error")
                    
        except Exception as e:
            raise Exception(f"Failed to submit registration form: {e}")
            
    async def _handle_verification(self, email: str) -> Dict[str, Any]:
        """Handle email verification process"""
        try:
            self.logger.info("Handling verification process...")
            
            # Check current page for verification requirements
            page_source = self.driver.page_source.lower()
            
            if "verify" in page_source or "confirmation" in page_source:
                self.logger.info("Email verification required")
                
                # Wait for verification email
                verification_result = await self._wait_for_verification_email(email)
                
                if verification_result['success']:
                    # Click verification link
                    verification_link = verification_result['verification_link']
                    
                    # Open verification link
                    self.driver.get(verification_link)
                    
                    # Wait for verification completion
                    await asyncio.sleep(random.uniform(3.0, 8.0))
                    
                    return {
                        'success': True,
                        'verification_required': True,
                        'verification_method': 'email',
                        'account_id': self._extract_account_id()
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Email verification failed'
                    }
            else:
                # No verification required
                return {
                    'success': True,
                    'verification_required': False,
                    'account_id': self._extract_account_id()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Verification handling failed: {e}"
            }
            
    async def _wait_for_verification_email(self, email: str) -> Dict[str, Any]:
        """Wait for and process verification email"""
        try:
            max_wait_time = 300  # 5 minutes
            check_interval = 10   # 10 seconds
            
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # Check for verification email
                emails = await self.email_manager.get_emails(email)
                
                for email_data in emails:
                    if self._is_verification_email(email_data):
                        verification_link = self._extract_verification_link(email_data)
                        if verification_link:
                            return {
                                'success': True,
                                'verification_link': verification_link
                            }
                            
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            return {
                'success': False,
                'error': 'Verification email timeout'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Verification email check failed: {e}"
            }
            
    def _is_verification_email(self, email_data: Dict[str, Any]) -> bool:
        """Check if email is a verification email"""
        subject = email_data.get('subject', '').lower()
        content = email_data.get('content', '').lower()
        
        verification_keywords = [
            'verify', 'confirm', 'activation', 'welcome to facebook',
            'complete your registration', 'click to confirm'
        ]
        
        return any(keyword in subject or keyword in content for keyword in verification_keywords)
        
    def _extract_verification_link(self, email_data: Dict[str, Any]) -> Optional[str]:
        """Extract verification link from email"""
        content = email_data.get('content', '')
        
        # Look for Facebook verification links
        import re
        link_patterns = [
            r'https://www\.facebook\.com/n/\?[^"\s]+',
            r'https://m\.facebook\.com/n/\?[^"\s]+',
            r'https://[^"\s]*facebook[^"\s]*confirm[^"\s]*',
            r'https://[^"\s]*facebook[^"\s]*verify[^"\s]*'
        ]
        
        for pattern in link_patterns:
            matches = re.findall(pattern, content)
            if matches:
                return matches[0]
                
        return None
        
    def _extract_account_id(self) -> Optional[str]:
        """Extract account ID from current page"""
        try:
            # Try to extract from URL
            current_url = self.driver.current_url
            
            # Look for user ID in URL
            import re
            id_patterns = [
                r'facebook\.com/profile\.php\?id=(\d+)',
                r'facebook\.com/(\d+)',
                r'id=(\d+)'
            ]
            
            for pattern in id_patterns:
                match = re.search(pattern, current_url)
                if match:
                    return match.group(1)
                    
            # Try to extract from page source
            page_source = self.driver.page_source
            
            # Look for user ID in JavaScript or meta tags
            js_patterns = [
                r'"USER_ID":"(\d+)"',
                r'"userID":"(\d+)"',
                r'user_id=(\d+)'
            ]
            
            for pattern in js_patterns:
                match = re.search(pattern, page_source)
                if match:
                    return match.group(1)
                    
        except Exception as e:
            self.logger.debug(f"Failed to extract account ID: {e}")
            
        return None
        
    async def _cleanup_browser(self):
        """Cleanup browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                
            self.current_proxy = None
            self.current_user_agent = None
            
        except Exception as e:
            self.logger.warning(f"Browser cleanup error: {e}")
            
    async def health_check(self) -> bool:
        """Check health of account creator"""
        try:
            # Check dependencies
            if not await self.proxy_manager.health_check():
                return False
            if not await self.user_agent_manager.health_check():
                return False
            if not await self.email_manager.health_check():
                return False
            if not await self.identity_manager.health_check():
                return False
            if not await self.behavior_simulator.health_check():
                return False
            if not await self.anti_detection.health_check():
                return False
                
            self.logger.info("Facebook Account Creator health check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Facebook Account Creator health check failed: {e}")
            return False

