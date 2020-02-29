#!/usr/bin/lua
local mqtt = require "libraries.mqtt.init"
local fileParser = require "libraries.file_parser"
local common = require "libraries.common"
local socket = require "libraries.socket"

function Path()
        local str = debug.getinfo(2, "S").source:sub(2)
        return str:match("(.*/)")
end

PATH = Path();
local configPath = PATH .. "broker.conf"


--pagrindiniai parametrai
local deviceMAC = "unknown"  --useruid/system/C493000EFE35/control

--nuskaitom is config failo
local userUID = fileParser.ReadFileData(configPath,"useruuid")
local systemName = fileParser.ReadFileData(configPath,"systemname")
local cafilePath = fileParser.ReadFileData(configPath,"cafile")
IsSignalLost = false

function Is_openwrt()
        return(os.getenv("USER") == "root" or os.getenv("USER") == nil)
end

if (Is_openwrt()) then 
        local handle = io.popen("ifconfig -a | grep mesh0 | head -1")
        local result = handle:read("*a")
        --jei prietaisas yra su openwrt OS, tuomet irasom prietaiso MAC adresa
        deviceMAC = string.match(result, "HWaddr(.*)")
        deviceMAC = deviceMAC:gsub("%:", "") --pasalinam dvitaskius
        deviceMAC = deviceMAC:gsub("%s+", "") --pasalinam tarpus
        handle:close()
end

--tema user/system/prietaisoMAC/duomenuTipas
local topic = userUID .. "/" .. systemName .. "/" .. deviceMAC .. "/jsondata"

--parametrai nuskaitomi is konfiguracinio failo
local brokerIP = fileParser.ReadFileData(configPath,"ip")
local delay = fileParser.ReadFileData(configPath,"delay")

function Main()
        --sukuriamas sujungimas su MQTT brokeriu       
        local parameters = {
                mode = "client",
                protocol = "tlsv1_2",
                cafile = cafilePath,
                verify = {"peer", "fail_if_no_peer_cert"},
                options = "all",
             }
        
        local client = mqtt.client{
                uri = brokerIP,
                clean = false,
                version = mqtt.v311,
                secure = parameters
        }
        
        print("Program starting...")        
               
        while true do
                local result = client:start_connecting()

                if result == false then
                        print("Connection to broker " .. brokerIP .. " failed:")
                        return
                else
                        print("Connection with MQTT broker " .. brokerIP .. " established!") -- sekmingas prijungimas
                        IsSignalLost = false
                end  

                local response = Loop(client,delay)

                --dingo signalas
                if(response == -2)then
                        client:close_connection()  
                        common.RestoreConnection("8.8.8.8") --bandom atstatyti rysi
                else --kitos priezastys                        
                        client:close_connection()                         
                        break
                end
        end
        print("Program stopped")  

        return
end

function Loop(client,sleepDelay)

        Running = true
        while (Running) do  
                local message = common.ReadData(deviceMAC)

                if (common.CheckPing("8.8.8.8") == true) then 
                        common.PublishData(client,topic,message)
                        socket.sleep(sleepDelay)
                else
                        print("Signal is lost.")
                        IsSignalLost = true
                        return -2
                end
        end 
end
--startuojam
Main()