import streamlit as st
import streamlit_antd_components as sac
from chatchat.webui_pages.utils import *
from chatchat.settings import Settings
import requests
import json



def mcp_management_page(api: ApiRequest, is_lite: bool = False):
    """
    MCP management page - connector settings interface.
    Designed in a hyper-sensory minimalism × liquid digital morphism style.
    Implemented with Streamlit.
    """

    # Initialize session state
    if 'mcp_profile_loaded' not in st.session_state:
        st.session_state.mcp_profile_loaded = False
    if 'mcp_connections_loaded' not in st.session_state:
        st.session_state.mcp_connections_loaded = False
    if 'mcp_connections' not in st.session_state:
        st.session_state.mcp_connections = []
    if 'mcp_profile' not in st.session_state:
        st.session_state.mcp_profile = {}

    if "show_add_conn" not in st.session_state:
        st.session_state.show_add_conn = False

    # Page CSS styles
    st.markdown("""
        <style>
            /* CSS variable definitions */
            :root {
                --accent-primary: linear-gradient(135deg, #4F46E5 0%, #818CF8 100%);
                --accent-warning: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
                --bg-nav: #F9FAFB;
                --bg-card: #FFFFFF;
                --text-primary: #111827;
                --text-secondary: #6B7280;
                --border-light: #E5E7EB;
                --shadow-hover: 0 8px 24px rgba(79, 70, 229, 0.1);
            }
            
            /* Global style reset */
            .stApp {
                background-color: #FAFAFA !important;
            }

            /* Hide Streamlit default elements */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display: none;}

            /* Navigation bar styles */
            .nav-container {
                background: var(--bg-nav);
                border-right: 1px solid var(--border-light);
                padding: 16px 8px;
                border-radius: 12px;
                margin-bottom: 24px;
            }
            
            .nav-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 16px;
                margin: 4px 0;
                color: var(--text-secondary);
                text-decoration: none;
                border-radius: 8px;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .nav-item:hover {
                background: rgba(0, 0, 0, 0.05);
            }
            
            .nav-item.active {
                background: var(--bg-card);
                color: var(--text-primary);
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                border-left: 3px solid #4F46E5;
            }
            
            /* Connector card styles */
            .connector-card {
                background: var(--bg-card);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 16px;
                border: 1px solid var(--border-light);
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .connector-card:hover {
                border-color: rgba(79, 70, 229, 0.2);
                box-shadow: var(--shadow-hover);
                transform: translateY(-2px);
            }
            
            .connector-card.warning {
                border-color: rgba(245, 158, 11, 0.2);
            }
            
            .connector-content {
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .connector-left {
                display: flex;
                align-items: center;
                gap: 16px;
            }
            
            .connector-icon {
                width: 48px;
                height: 48px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 20px;
                color: white;
                flex-shrink: 0;
            }
            
            .connector-info h3 {
                margin: 0 0 4px 0;
                font-size: 16px;
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .connector-info p {
                margin: 0;
                font-size: 12px;
                color: var(--text-secondary);
            }
            
            .status-indicator {
                display: flex;
                align-items: center;
                gap: 6px;
                margin-top: 8px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--accent-warning);
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            /* Browse connector card styles */
            .browse-card {
                background: var(--bg-card);
                border-radius: 12px;
                padding: 24px;
                border: 1px solid var(--border-light);
                text-align: center;
                transition: all 0.3s ease;
                cursor: pointer;
                height: 100%;
            }
            
            .browse-card:hover {
                border-color: rgba(79, 70, 229, 0.3);
                box-shadow: var(--shadow-hover);
                transform: scale(1.03);
            }
            
            .browse-icon {
                width: 56px;
                height: 56px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 12px;
                transition: transform 0.5s ease;
            }
            
            .browse-card:hover .browse-icon {
                transform: scale(1.1);
            }
            
            .browse-card h3 {
                margin: 0;
                font-size: 14px;
                font-weight: 500;
                color: var(--text-primary);
            }
            
            /* Page title styles */
            .page-title {
                font-size: 24px;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 32px;
            }
            
            /* Section title styles */
            .section-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--text-primary);
                margin: 32px 0 16px 0;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .connector-content {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 12px;
                }
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Page layout
    with st.container():
        # Page title
        st.markdown('<h1 class="page-title">Connector Management</h1>', unsafe_allow_html=True)

        # General settings section
        with st.expander("General Settings", expanded=False):

            # Load the current configuration
            if not st.session_state.mcp_profile_loaded:
                try:
                    profile_data = api.get_mcp_profile()
                    if profile_data:
                        st.session_state.mcp_profile = profile_data
                        # Initialize environment variable list
                        env_vars = st.session_state.mcp_profile.get("env_vars", {})
                        st.session_state.env_vars_list = [
                            {"key": k, "value": v} for k, v in env_vars.items()
                        ]
                        st.session_state.mcp_profile_loaded = True
                    else:
                        # Use defaults
                        st.session_state.mcp_profile = {
                            "timeout": 30,
                            "working_dir": str(Settings.CHATCHAT_ROOT),
                            "env_vars": {
                                "PATH": "/usr/local/bin:/usr/bin:/bin",
                                "PYTHONPATH": "/app",
                                "HOME": str(Settings.CHATCHAT_ROOT)
                            }
                        }
                        st.session_state.env_vars_list = [
                            {"key": "PATH", "value": "/usr/local/bin:/usr/bin:/bin"},
                            {"key": "PYTHONPATH", "value": "/app"},
                            {"key": "HOME", "value": str(Settings.CHATCHAT_ROOT)}
                        ]
                except Exception as e:
                    st.error(f"Failed to load configuration: {str(e)}")
                    return

            # Default timeout setting
            timeout_value = st.slider(
                "Default connection timeout (seconds)",
                min_value=10,
                max_value=300,
                value=st.session_state.mcp_profile.get("timeout", 30),
                step=5,
                help="Set the default timeout for MCP connectors. Range: 10-300 seconds"
            )

            # Working directory setting
            working_dir = st.text_input(
                "Default working directory",
                value=st.session_state.mcp_profile.get("working_dir", str(Settings.CHATCHAT_ROOT)),
                help="Set the default working directory for MCP connectors"
            )
            # Environment variable setting
            st.subheader("Environment Variable Configuration")

            # Edit environment variable key-value pairs
            st.write("Add environment variable key-value pairs:")

            # Initialize environment variable list
            if 'env_vars_list' not in st.session_state:
                st.session_state.env_vars_list = [
                    {"key": "PATH", "value": "/usr/local/bin:/usr/bin:/bin"},
                    {"key": "PYTHONPATH", "value": "/app"},
                    {"key": "HOME", "value": str(Settings.CHATCHAT_ROOT)}
                ]
            
            # Show existing environment variables
            for i, env_var in enumerate(st.session_state.env_vars_list):
                col1, col2, col3 = st.columns([2, 3, 1])

                with col1:
                    key = st.text_input(
                        "Variable name",
                        value=env_var["key"],
                        key=f"env_key_{i}",
                        placeholder="e.g., PATH"
                    )
                    env_var["key"] = key
                with col2:
                    value = st.text_input(
                        "Variable value",
                        value=env_var["value"],
                        key=f"env_value_{i}",
                        placeholder="e.g., /usr/bin"
                    )

                    env_var["value"] = value
                with col3:
                    if st.button("Delete", key=f"env_delete_{i}", help="Delete this environment variable"):
                        st.session_state.env_vars_list.pop(i)
                        # Immediately save to the database after deletion
                        try:
                            env_vars_dict = {}
                            for env_var in st.session_state.env_vars_list:
                                if env_var["key"] and env_var["value"]:
                                    env_vars_dict[env_var["key"]] = env_var["value"]

                            result = api.update_mcp_profile(
                                timeout=timeout_value,
                                working_dir=working_dir,
                                env_vars=env_vars_dict
                            )

                            # Update values
                            if key != env_var["key"] or value != env_var["value"]:
                                st.session_state.env_vars_list[i] = {"key": key, "value": value}
                        except Exception as e:
                            st.error(f"Delete failed: {str(e)}")
                        st.rerun()

            # Add new environment variable button
            if st.button("Add Environment Variable", key="add_env_var"):
                st.session_state.env_vars_list.append({"key": "", "value": ""})
                st.rerun()

            # Show current environment variable preview
            if st.session_state.env_vars_list:
                st.markdown("### Current Environment Variables")
                env_preview = {}
                for env_var in st.session_state.env_vars_list:
                    if env_var["key"] and env_var["value"]:
                        env_preview[env_var["key"]] = env_var["value"]

                st.code(
                    "\n".join([f'{k}="{v}"' for k, v in env_preview.items()]),
                    language="bash",
                    line_numbers=False
                )
            else:
                st.info("No environment variables configured yet")


            # Save settings button
            col1, col2 = st.columns([1, 2])

            with col1:
                if st.button("Save Settings", type="primary", use_container_width=True):
                    try:
                        # Build the environment variables dictionary
                        env_vars_dict = {}
                        for env_var in st.session_state.env_vars_list:
                            if env_var["key"] and env_var["value"]:
                                env_vars_dict[env_var["key"]] = env_var["value"]

                        # Save to the database
                        result = api.update_mcp_profile(
                            timeout=timeout_value,
                            working_dir=working_dir,
                            env_vars=env_vars_dict
                        )

                        if result:
                            st.success("General settings saved")
                            st.session_state.mcp_profile['timeout'] = timeout_value
                            st.session_state.mcp_profile['working_dir'] = working_dir
                            st.session_state.mcp_profile_loaded = False  # Reload
                        else:
                            st.error("Save failed; please check the configuration")
                    except Exception as e:
                        st.error(f"Save failed: {str(e)}")

            with col2:
                if st.button("Reset to Defaults", use_container_width=True):
                    try:
                        result = api.reset_mcp_profile()
                        if result and result.get("success"):
                            # Reset UI state
                            st.session_state.env_vars_list = [
                                {"key": "PATH", "value": "/usr/local/bin:/usr/bin:/bin"},
                                {"key": "PYTHONPATH", "value": "/app"},
                                {"key": "HOME", "value": str(Settings.CHATCHAT_ROOT)}
                            ]
                            st.session_state.mcp_profile_loaded = False
                            st.rerun()
                        else:
                            st.error("Reset failed")
                    except Exception as e:
                        st.error(f"Reset failed: {str(e)}")


        # Connector navigation
        st.markdown('<h2 class="section-title">Connector Management</h2>', unsafe_allow_html=True)

        # Load MCP connection data
        if not st.session_state.mcp_connections_loaded:
            try:
                connections_data = api.get_all_mcp_connections()
                if connections_data:
                    st.session_state.mcp_connections = connections_data.get("connections", [])
                    st.session_state.mcp_connections_loaded = True
                else:
                    st.session_state.mcp_connections = []
            except Exception as e:
                st.error(f"Failed to load connectors: {str(e)}")
                return

        # Enabled connectors section
        st.markdown('<h2 class="section-title">Enabled Connectors</h2>', unsafe_allow_html=True)

        # Show enabled connectors
        enabled_connections = [conn for conn in st.session_state.mcp_connections if conn.get("enabled", False)]

        if enabled_connections:
            for connection in enabled_connections:
                # Generate connector icon colors
                icon_colors = {
                    "stdio": "#111827",
                    "sse": "linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%)"
                }
                
                # Use transport type as the icon identifier
                transport = connection.get("transport", "stdio").lower()
                icon_letter = "S" if transport == "stdio" else "E"
                icon_bg = icon_colors.get("stdio", "linear-gradient(135deg, #4F46E5 0%, #818CF8 100%)") if transport == "stdio" else icon_colors.get("sse", "linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%)")

                # Connector card
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                            <div class="connector-card">
                                <div class="connector-content">
                                    <div class="connector-left">
                                        <div class="connector-icon" style="background: {icon_bg};">
                                            <span>{icon_letter}</span>
                                        </div>
                                        <div class="connector-info">
                                            <h3>{connection.get('server_name', '')}</h3>
                                            <p>{json.dumps(connection.get('config', {}), ensure_ascii=False, indent=2)}</p>
                                            <div class="status-indicator">
                                                <div class="status-dot" style="background: #6B7280;"></div>
                                                <span style="color: #6B7280; font-size: 12px; font-weight: 500;">Connected</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("Disable", key=f"toggle_disable_{connection.get('id', i)}", use_container_width=True):
                            toggle_connection_status(api, connection.get('id', i), False)
        else:
            st.info("No enabled connectors yet")

        # Browse connectors section
        st.markdown('<h2 class="section-title">Browse Connectors</h2>', unsafe_allow_html=True)

        # Show all connectors (including disabled ones)
        disabled_connections = [conn for conn in st.session_state.mcp_connections if not conn.get("enabled", True)]

        if disabled_connections:
            # Connector grid
            cols = st.columns(3)

            for i, connection in enumerate(disabled_connections):
                with cols[i % 3]:
                    # Generate connector icon
                    icon_emojis = {
                        "stdio": "[stdio]",
                        "sse": "[sse]"
                    }

                    transport = connection.get("transport", "stdio").lower()
                    icon_emoji = icon_emojis.get(transport, "[link]")

                    # Connector card
                    st.markdown(f"""
                        <div class="browse-card">
                            <div class="browse-icon" style="background: rgba(107, 114, 128, 0.1);">
                                <span style="color: #6B7280; font-size: 24px;">{icon_emoji}</span>
                            </div>
                            <h3>{connection.get('server_name', '')}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Enable", key=f"toggle_enable_{connection.get('id', i)}", use_container_width=True):
                        toggle_connection_status(api, connection.get('id', i), True)
        else:
            st.info("No other connectors yet")

    # Add some interactive features
    st.divider()

    # Connector actions area
    st.subheader("Connector Actions")

    # Click only changes state; re-runs immediately
    if st.button("Add New Connector", type="primary"):
        st.session_state.show_add_conn = True
        st.rerun()

    # Use a placeholder container to hold the "dialog content"
    placeholder = st.empty()
    if st.session_state.show_add_conn:
        with placeholder.container():
            add_new_connection_form(api)     # The form itself
    # Add some explanatory information
    st.divider()

    with st.expander("Usage Instructions", expanded=False):
        st.markdown("""
        ### Connector Management

        **Enabled connectors**: shows connectors that are currently configured and enabled; click to access detailed settings.

        **Browse connectors**: displays available connector types; click to quickly add and configure.

        **Status indicators**:
        - OK - running normally
        - Warning - setup incomplete or misconfigured
        - Failed - connection failed

        **Supported connector types**:
        - Document collaboration: Canva, Notion
        - Code hosting: GitHub
        - Communication tools: Gmail, Slack
        - Cloud storage: Box, Google Drive
        - Social media: Twitter
        """)

    # Footer info
    st.markdown("---")
    st.caption("Tip: connectors require proper API permissions and network access to work correctly")


def add_new_connection_form(api: "ApiRequest"):
    """
    Dialog form for adding a new connector (revised).
    - Uses st.form throughout to ensure single-shot submission
    - Robust Session State initialization
    - Displays different required fields depending on transport
    """
    import streamlit as st

    # ---- State initialization ----
    if "connection_args" not in st.session_state:
        st.session_state.connection_args = []
    if "connection_env_vars" not in st.session_state:
        # Shape: [{"key":"FOO","value":"bar"}]
        st.session_state.connection_env_vars = st.session_state.env_vars_list or []

    st.subheader("New Connector Configuration")

    with st.form("new_mcp_connection"):
        # ===== Basic information =====
        col1, col2 = st.columns(2)
        with col1:
            server_name = st.text_input(
                "Server name *",
                placeholder="e.g., my-server",
                help="The unique identifier for the server",
                key="conn_server_name",
            )
        with col2:
            transport = st.selectbox(
                "Transport *",
                options=["sse", "stdio"],
                help="Connection transport protocol",
                key="conn_transport",
            )

        # ===== Startup command / SSE configuration =====
        st.subheader("Transport Configuration")
        # Always give command a default value to avoid being undefined
        command = ""

        if transport == "stdio":
            command = st.text_input(
                "Startup command *",
                placeholder="e.g., python -m mcp_server",
                help="Command to start the MCP server",
                key="conn_command",
            )

            # Stdio-specific configuration
            st.subheader("Stdio Transport Configuration")
            encoding = st.selectbox(
                "Text encoding",
                options=["utf-8", "gbk", "ascii", "latin-1"],
                index=0,
                help="Text encoding format",
                key="conn_encoding",
            )

            encoding_error_handler = st.selectbox(
                "Encoding error handler",
                options=["strict", "ignore", "replace"],
                index=0,
                help="How to handle encoding errors",
                key="conn_encoding_error_handler",
            )
        else:
            # SSE mode typically requires a URL; adjust the field name as needed for your backend
            sse_url = st.text_input(
                "SSE server URL *",
                placeholder="e.g., https://example.com/mcp/sse",
                help="URL of the SSE server",
                key="conn_sse_url",
            )

            # SSE-specific configuration
            st.subheader("SSE Transport Configuration")

            # Optional: extra SSE headers
            sse_headers = st.text_area(
                "SSE Headers (optional, JSON)",
                placeholder='e.g., {"Authorization":"Bearer xxx"}',
                help="Provide optional request headers as JSON",
                key="conn_sse_headers",
            )

            col_ti1, col_ti2 = st.columns(2)
            with col_ti1:

                sse_encoding_error_handler = st.selectbox(
                    "Encoding error handler",
                    options=["strict", "ignore", "replace"],
                    index=0,
                    help="How to handle encoding errors",
                    key="conn_sse_encoding_error_handler",
                )

            with col_ti2:

                # SSE encoding configuration
                sse_encoding = st.selectbox(
                    "Text encoding",
                    options=["utf-8", "gbk", "ascii", "latin-1"],
                    index=0,
                    help="Text encoding format",
                    key="conn_sse_encoding",
                )

        # ===== Command arguments (optional) =====
        st.write("Command arguments (optional):")
        # Show already-added arguments
        for i, arg in enumerate(st.session_state.connection_args):
            col_arg, col_del = st.columns([4, 1])
            with col_arg:
                new_arg = st.text_input(
                    f"Argument {i+1}",
                    value=arg,
                    key=f"conn_arg_{i}",
                    placeholder="e.g., --port=8080",
                )
                if new_arg != arg:
                    st.session_state.connection_args[i] = new_arg
            with col_del:
                # Note: buttons inside a form also trigger form submission, so we use a different key and only modify state
                if st.form_submit_button(f"Delete_{i}", use_container_width=True):
                    st.session_state.connection_args.pop(i)
                    st.rerun()

        # Add argument button (inside the form)
        if st.form_submit_button("Add Argument", use_container_width=False):
            st.session_state.connection_args.append("")
            st.rerun()

        # ===== Environment variables (optional) =====
        st.write("Environment variables (optional):")
        # Show already-added envs
        for i, pair in enumerate(st.session_state.connection_env_vars):
            col_k, col_v, col_del = st.columns([3, 4, 1])
            with col_k:
                new_k = st.text_input(
                    f"Key {i+1}",
                    value=pair.get("key", ""),
                    key=f"env_k_{i}",
                    placeholder="e.g., GITHUB_TOKEN",
                )
            with col_v:
                new_v = st.text_input(
                    f"Value {i+1}",
                    value=pair.get("value", ""),
                    key=f"env_v_{i}",
                    placeholder="e.g., xxxxxx",
                    type="password",
                )
            with col_del:
                if st.form_submit_button(f"Delete ENV_{i}", use_container_width=True):
                    st.session_state.connection_env_vars.pop(i)
                    st.rerun()
            # Sync changes
            st.session_state.connection_env_vars[i] = {"key": new_k, "value": new_v}

        # Add ENV button
        if st.form_submit_button("Add Environment Variable"):
            st.session_state.connection_env_vars.append({"key": "", "value": ""})
            st.rerun()

        # ===== Advanced settings =====
        with st.expander("Advanced Settings", expanded=False):
            col_adv1, col_adv2 = st.columns(2)
            with col_adv1:
                timeout = st.number_input(
                    "Connection timeout (seconds)",
                    min_value=10,
                    max_value=300,
                    value=st.session_state.mcp_profile.get("timeout", 30),
                    help="Connection timeout",
                    key="conn_timeout",
                )
                cwd = st.text_input(
                    "Working directory",
                    value=st.session_state.mcp_profile.get("working_dir", str(Settings.CHATCHAT_ROOT)),
                    placeholder="/tmp",
                    help="Working directory for the server process",
                    key="conn_cwd",
                )
            with col_adv2:
                enabled = st.checkbox(
                    "Enable connector",
                    value=False,
                    help="Whether to enable this connector",
                    key="conn_enabled",
                )

        # ===== Description =====
        description = st.text_area(
            "Connector description",
            placeholder="Describe the purpose and configuration of this connector...",
            help="Optional connector description",
            key="conn_description",
        )

        # ===== Submit / Cancel =====
        col_submit, col_cancel = st.columns([1, 1])
        with col_submit:
            submitted = st.form_submit_button("Create Connector", type="primary", use_container_width=True)
        with col_cancel:
            cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)

        # ----- Submission handling -----
        if cancel_clicked:
            # Clean up state and refresh
            st.session_state.connection_args = []
            st.session_state.connection_env_vars = []
            st.session_state.show_add_conn = False
            st.rerun()

        if submitted:
            # Validate
            errors = []
            if not server_name:
                errors.append("Server name")

            if transport == "stdio":
                if not command:
                    errors.append("Startup command (stdio)")
            else:
                if not sse_url:
                    errors.append("SSE server URL")

            if errors:
                st.error("Please fill in all required fields (*): " + ", ".join(errors))
                return

            # Parse env
            env_vars_dict = {}
            for env_var in st.session_state.connection_env_vars:
                k = (env_var.get("key") or "").strip()
                v = (env_var.get("value") or "").strip()
                if k and v:
                    env_vars_dict[k] = v

            # Build API parameters
            payload = dict(
                server_name=server_name,
                args=st.session_state.connection_args,
                env=env_vars_dict,
                cwd=cwd or "",
                transport=transport,
                timeout=timeout,               # pass integer
                enabled=bool(enabled),
                description=description or None,
                config={},                     # reserved
            )

            if transport == "stdio":
                # Add command to config instead of payload root
                payload["config"]["command"] = command
                # Add stdio-specific config
                payload["config"]["encoding"] = encoding
                payload["config"]["encoding_error_handler"] = encoding_error_handler
            else:
                # SSE transport - store SSE-specific fields in config
                payload["config"]["url"] = sse_url
                if sse_headers:
                    # Try to parse as JSON; on failure treat as raw text
                    import json
                    try:
                        payload["config"]["headers"] = json.loads(sse_headers)
                    except Exception as e:
                        st.error(f"sse_headers error: {e}")
                else:
                    payload["config"]["headers"] = None

                # Set encoding config for SSE
                payload["config"]["encoding"] = sse_encoding
                payload["config"]["encoding_error_handler"] = sse_encoding_error_handler

            try:
                result = api.add_mcp_connection(**payload)
                # Convention: True / non-empty dict is treated as success
                if result:
                    st.success("Connector created successfully!")
                    # Clean up and refresh the list
                    st.session_state.connection_args = []
                    st.session_state.connection_env_vars = []
                    st.session_state.mcp_connections_loaded = False
                    st.session_state.show_add_conn = False
                    st.rerun()
                else:
                    st.error(f"Creation failed: {getattr(result,'msg', None) or (result.get('msg') if isinstance(result, dict) else 'unknown error')}")
            except Exception as e:
                st.error(f"Error while creating connector: {e}")

def toggle_connection_status(api: ApiRequest, connection_id: str, enabled: bool):
    """
    Toggle connector enabled/disabled state
    """
    try:
        result = api.update_mcp_connection(connection_id=connection_id, enabled=enabled)
        if result and result.get("success"):
            status = "enabled" if enabled else "disabled"
            st.success(f"Connector {status} successfully!")
            st.session_state.mcp_connections_loaded = False  # Reload the connection list
            st.rerun()
        else:
            status = "enable" if enabled else "disable"
            st.error(f"Failed to {status}: {result.get('message', 'unknown error')}")
    except Exception as e:
        status = "enabling" if enabled else "disabling"
        st.error(f"Error while {status} connector: {str(e)}")

def delete_connection(api: ApiRequest, connection_id: str):
    """
    Delete a connector
    """
    try:
        result = api.delete_mcp_connection(connection_id=connection_id)
        if result and result.get("code") == 200:
            st.success("Connector deleted successfully!")
            st.session_state.mcp_connections_loaded = False  # Reload the connection list
            st.rerun()
        else:
            st.error(f"Delete failed: {result.get('msg', 'unknown error')}")
    except Exception as e:
        st.error(f"Error while deleting connector: {str(e)}")