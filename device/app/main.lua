#!/usr/bin/lua

local socket = require("socket")
local http = require("socket.http")
local MQTT = require("mqtt_library")
local json = require("json")
local deviceMAC = "unknown"
local userUID = "useruid"
local systemName = "system"

function Is_openwrt()
        return(os.getenv("USER") == "root" or os.getenv("USER") == nil)
end

if (Is_openwrt()) then 
        local handle = io.popen("ifconfig -a | grep wlan0 | head -1")
        local result = handle:read("*a")
        deviceMAC = string.match(result, "HWaddr(.*)")
        deviceMAC = deviceMAC:gsub("%:", "") --pasalinam dvitaskius
        deviceMAC = deviceMAC:gsub("%s+", "") --pasalinam tarpus
        handle:close()
end

function GetPublicIP()
        --is ipinfo.io gaunam json objekta
        local resp,code = http.request("http://ipinfo.io/json")
        
        --jei uzklausos kodas yra ne 200 (success)
        if code ~= 200 
        then 
                return nil 
        end

        --dekoduojam atsakymo json
        local data = json.decode(resp)
        if data ~= nil
        then                
                if data.ip ~= nil
                then
                        return data.ip --Realus ip adresas
                else
                        return nil
                end 
        else
                return nil
        end  
                
end

--MQTT callbackas
Running = false  
function Callback(topic, message)
        print("Received: " .. topic .. ": " .. message)
        if (message == "quit") then Running = false end
end

--MQTT publish
function PublishData(mqtt_client,topic,message,deviceName)
        MQTT.Utility.set_debug(true)
        mqtt_client:connect(deviceName)
        
        mqtt_client:handler()
        mqtt_client:publish(topic,message)
        socket.sleep(5.0)  -- seconds        
end

function Main()
        --sukuriamas sujungimas su MQTT brokeriu
        local mqtt_client = MQTT.client.create("192.168.137.53", nil, callback)

        --kol nenutraukiamas rysys, tol sukasi
        Running = true
        while (Running) do
                --duomenu nuskaitymas, etc                
                local innerTemp = 252.25  --test
                local heater_1_state = true
                local heater_2_state = false
                local heater_3_state = false
                local fanState = true
                local outerTemp = ReadFileData("test.txt","temp")

                --formuojama duomenu lenta, kuri veliau parsinama i 
                local dataTable = { 
                        deviceMAC=deviceMAC,
                        innerTemp=innerTemp,
                        outerTemp=outerTemp,
                        heaterStates={
                                heater_1=heater_1_state,
                                heater_2=heater_2_state,
                                heater_3=heater_3_state
                                },
                        fanState = fanState
                        }

                local Message = json.encode(dataTable)
                --tema user/system/prietaisoMAC/
                Topic = userUID .. "/" .. systemName .. "/" .. deviceMAC .. "/jsondata"

                print(Topic)
                print(Message)
                --local IP = GetPublicIP()
                --print(IP)                
               
                --publishingas
                PublishData(mqtt_client,Topic,Message,"MQTT publisher " .. deviceMAC)
        end

        mqtt_client:destroy()
        return
end

function ReadFileData(pathToFile, type)
        local file, err = io.open(pathToFile,"r")
        if err then print("File is empty"); return; end
        local data = ""
        while true do
                local line = file:read()                
                if line == nil then break else data = data .. line end
        end        
        file:close()

        local result = nil

        --Isparsinam is failo temperatura
        if type == "temp"
        then
                local temperature = string.match(data, "t=(.*)")
                result = temperature / 1000
        end

        return result
end

Main()