local json = require "libraries.json"
local fileParser = require "libraries.file_parser"
local serialController = require "libraries.rs232_controller"
local socket = require "libraries.socket"
local aes = require "libraries.cryptography"

local common = {}


function common.sleep(s)  -- seconds
    socket.sleep(s)
end

--MQTT publish
function common.PublishData(client,topic,message,aesKey)
    local payload = aes.encrypt(aesKey, message)
    client:publish{
            topic = topic,
            payload = payload,
            qos = 0,
            properties = {
                    payload_format_indicator = 1,
                    content_type = "json",
            },
    }     
end

function common.RestoreConnection(ip)
        
    print("Trying to restore connection...")                
    while (common.CheckPing(ip) == false) do
            socket.sleep(5.0)
    end

    IsSignalLost = false
    print("Connection with " .. ip .. " restored!")
    io.popen("./run_daemon.sh reboot")
    return true
end

function common.CheckPing(IP)
    local command = "ping -c 1 -W 1 " .. IP
    local handler = io.popen(command)
    local response = handler:read("*a")
    handler:close()
    
    if (string.match(response, " 0%% packet loss") and 
    not string.match(response, "Network unreachable")) 
    then return true else return false end
end

function common.ReadData(deviceMAC)
    --gaunami duomenys per UART sasaja is arduino    
    local rawData = string.match(serialController.Get_serial_data("/dev/ttyUSB0"),"([^;]+)")
    local data = {}

    for str in string.gmatch(rawData , "([^:]+)") do        
        local name = string.match(str , "([^=]+)")
        local value = string.match(str , "=(.*)")

        data[name] = value
    end

    --formuojama duomenu lenta, kuri veliau parsinama i jsona
    local dataTable = { 
        deviceMAC=deviceMAC,
        data=data
        }            
    
    return json.encode(dataTable)
end

function common.ResponseJson(success, message, reason)
    --formuojama duomenu lenta, kuri veliau parsinama i jsona
    local response = { 
        success=success,
        message=message,
        reason=reason
        }      
    return json.encode(response)
end

function common.GetLocalIP()
    local command = "ifconfig br-mesh | grep -i mask | grep -o '[0-9]\\{1,3\\}\\.[0-9]\\{1,3\\}\\.[0-9]\\{1,3\\}\\.[0-9]\\{1,3\\}' | head -n 1" 
    local handler = io.popen(command)
    local response = handler:read("*a")
    handler:close()  

    if response == nil then 
        response = 'N/A' 
    end

    response = string.gsub(response, '^%s*(.-)%s*$', '%1')

    return response
end

return common