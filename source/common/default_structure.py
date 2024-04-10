from common.keys import *

def create_default_structure():
    return {
            KEY_IMPORTS         : {KEY_NAME : None,             KEY_BODY : None,  KEY_SELF: False},
            KEY_MAIN            : {KEY_NAME : None,             KEY_BODY : None,  KEY_SELF: False},
            KEY_STATES          : {KEY_NAME : None,             KEY_BODY : None,  KEY_SELF: False},
            KEY_CLASS_NAME      : {KEY_NAME : None,             KEY_BODY : None,  KEY_SELF: False},
            KEY_RUN             : {KEY_NAME : "run",            KEY_BODY : None,  KEY_SELF: True},
            KEY_MESSAGE_HANDLER : {KEY_NAME : "handle_message", KEY_BODY : None,  KEY_SELF: True},
            KEY_RUN_SERVER      : {KEY_NAME : "run_server",     KEY_BODY : None,  KEY_SELF: True},
            KEY_RUN_CLIENT      : {KEY_NAME : "run_client",     KEY_BODY : None,  KEY_SELF: True},
            KEY_RUN_MODEL       : {KEY_NAME : "run_model",      KEY_BODY : None,  KEY_SELF: True},
            KEY_INHERIT         : {
                KEY_PRIVATE     : {KEY_NAME : None,             KEY_BODY : [],  KEY_SELF: False},
                KEY_PUBLIC      : {KEY_NAME : None,             KEY_BODY : [],  KEY_SELF: False}
            },
            KEY_CONSTRUCTOR     : {
                KEY_PRIVATE     : {KEY_NAME : None,             KEY_BODY : None,  KEY_SELF: True},
                KEY_PUBLIC      : {KEY_NAME : None,             KEY_BODY : None,  KEY_SELF: True}
            },
            KEY_DESTRUCTOR      : {
                KEY_PRIVATE     : {KEY_NAME : None,             KEY_BODY : None,  KEY_SELF: True},
                KEY_PUBLIC      : {KEY_NAME : None,             KEY_BODY : None,  KEY_SELF: True}
            },
            KEY_MEMBER          : {
                KEY_PRIVATE     : {KEY_NAME : None,             KEY_BODY : [],  KEY_SELF: False},
                KEY_PUBLIC      : {KEY_NAME : None,             KEY_BODY : [],  KEY_SELF: False}
            },
            KEY_METHOD          : {
                KEY_PRIVATE     : {KEY_NAME : None,             KEY_BODY : [],  KEY_SELF: True},
                KEY_PUBLIC      : {KEY_NAME : None,             KEY_BODY : [],  KEY_SELF: True}
            },
            KEY_PARSE : {
                KEY_STOP        : {KEY_NAME : "parse_stop",       KEY_BODY : None, KEY_SELF : True},
                KEY_START       : {KEY_NAME : "parse_start",      KEY_BODY : None, KEY_SELF : True},
                KEY_SET_INPUT   : {KEY_NAME : "parse_set_input",  KEY_BODY : None, KEY_SELF : True},
                KEY_GET_OUTPUT  : {KEY_NAME : "parse_get_output", KEY_BODY : None, KEY_SELF : True},
                KEY_ADVANCE     : {KEY_NAME : "parse_advance",    KEY_BODY : None, KEY_SELF : True},
                KEY_INITIALIZE  : {KEY_NAME : "parse_initialize", KEY_BODY : None, KEY_SELF : True},
                KEY_MODEL_INFO  : {KEY_NAME : "parse_model_info", KEY_BODY : None, KEY_SELF : True},
                KEY_PUBLISH     : {KEY_NAME : "parse_initialize", KEY_BODY : None, KEY_SELF : True},
                KEY_SUBSCRIBE   : {KEY_NAME : "parse_model_info", KEY_BODY : None, KEY_SELF : True},
                KEY_GET_STATUS  : {KEY_NAME : "get_status",       KEY_BODY : None, KEY_SELF: True},
                KEY_SET_PARAMETER   : {KEY_NAME : "parse_set_param",  KEY_BODY : None, KEY_SELF : True},
                KEY_GET_PARAMETER   : {KEY_NAME : "parse_get_param",  KEY_BODY : None, KEY_SELF : True},
            },
            KEY_CALLBACK : {
                KEY_IMPORTS     : {KEY_NAME : None,                   KEY_BODY : None, KEY_SELF: False},
                KEY_CONSTRUCTOR : {KEY_NAME : None,                   KEY_BODY : None, KEY_SELF: False},
                KEY_MEMBER      : {KEY_NAME : None,                   KEY_BODY : None, KEY_SELF: False},
                KEY_METHOD      : {KEY_NAME : None,                   KEY_BODY : None, KEY_SELF: False},
                KEY_DESTRUCTOR  : {KEY_NAME : None,                   KEY_BODY : None, KEY_SELF: False},
                KEY_RUN         : {KEY_NAME : "run",                  KEY_BODY : None, KEY_SELF: True},
                KEY_RUN_MODEL   : {KEY_NAME : "run_model",            KEY_BODY : None, KEY_SELF: True},
                KEY_RUN_SERVER  : {KEY_NAME : "run_server",           KEY_BODY : None, KEY_SELF: True},
                KEY_RUN_CLIENT  : {KEY_NAME : "run_client",           KEY_BODY : None, KEY_SELF: True},
                KEY_STOP        : {KEY_NAME : "stop_callback",        KEY_BODY : None, KEY_SELF: True},
                KEY_START       : {KEY_NAME : "start_callback",       KEY_BODY : None, KEY_SELF: True},
                KEY_SET_INPUT   : {KEY_NAME : "set_input_callback",   KEY_BODY : None, KEY_SELF: True},
                KEY_GET_OUTPUT  : {KEY_NAME : "get_output_callback",  KEY_BODY : None, KEY_SELF: True},
                KEY_ADVANCE     : {KEY_NAME : "advance_callback",     KEY_BODY : None, KEY_SELF: True},
                KEY_INITIALIZE  : {KEY_NAME : "initialize_callback",  KEY_BODY : None, KEY_SELF: True},
                KEY_MODEL_INFO  : {KEY_NAME : "model_info_callback",  KEY_BODY : None, KEY_SELF: True},
                KEY_PUBLISH     : {KEY_NAME : "setup_subscribers",    KEY_BODY : None, KEY_SELF: True},
                KEY_SUBSCRIBE   : {KEY_NAME : "setup_publishers",     KEY_BODY : None, KEY_SELF: True},
                KEY_GET_STATUS  : {KEY_NAME : "get_status_callback",   KEY_BODY : None, KEY_SELF: True},
                KEY_SET_PARAMETER   : {KEY_NAME : "set_param_callback",   KEY_BODY : None, KEY_SELF: True},
                KEY_GET_PARAMETER   : {KEY_NAME : "get_param_callback",   KEY_BODY : None, KEY_SELF: True},
            },
            KEY_NEW             : {},
        }