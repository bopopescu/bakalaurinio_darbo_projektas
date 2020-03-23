--[[
    AES 256bit CTR duomenu sifravimas naudojant lockbox primitives
    iv - masyvas
    key - AES rakto HEXas
    data - encrypt funkcijoje string, o decrypt HEX
]]

local String = require("string");
local Array = require("libraries.lockbox.util.array");
local Stream = require("libraries.lockbox.util.stream");
local ECBMode = require("libraries.lockbox.cipher.mode.ecb");
local CBCMode = require("libraries.lockbox.cipher.mode.cbc");
local CFBMode = require("libraries.lockbox.cipher.mode.cfb");
local OFBMode = require("libraries.lockbox.cipher.mode.ofb");
local CTRMode = require("libraries.lockbox.cipher.mode.ctr");
local IGEMode = require("libraries.lockbox.cipher.mode.ige");
local ZeroPadding = require("libraries.lockbox.padding.zero");
local AES256Cipher = require("libraries.lockbox.cipher.aes256");
local json = require "libraries.json"

local crypto = {}

function string.fromhex(str)
    return (str:gsub('..', function (cc)
        return string.char(tonumber(cc, 16))
    end))
end

function string.tohex(str)
    return (str:gsub('.', function (c)
        return string.format('%02X', string.byte(c))
    end))
end

function crypto.encrypt(key,data)
    --generuojamas inicializacinis vektorius
    local iv = crypto.generateIV()
    local message = data .. ";"
    local chiperData = {
        cipher = CTRMode.Cipher,
        iv = iv,
        key = Array.fromHex(key),
        plaintext = Array.fromHex(string.tohex(message)),
        padding = ZeroPadding
    }
    
    --uzsifruojamas
    local cipher = assert(chiperData.cipher()
            .setKey(chiperData.key)
            .setBlockCipher(AES256Cipher)
            .setPadding(chiperData.padding));

    local cipherOutput = assert(cipher
            .init()
            .update(Stream.fromArray(chiperData.iv))
            .update(Stream.fromArray(chiperData.plaintext))
            .finish()
            .asHex());

    --suformuojamas krovinys
    local payload = {
        data = cipherOutput,
        iv = iv
    }  

    --konvertuojama i json
    return json.encode(payload)
end

function crypto.generateIV()
    local iv = {}
    math.randomseed(os.time())
    for i=1,16 do        
        table.insert(iv,math.random(0,255))
    end
    return iv
end

function crypto.decrypt(iv,key,data)
    if key == nil then 
        print("No key given.")
        return nil
    end

    local chiperData = {
        decipher = CTRMode.Decipher,
        iv = iv,
        key = Array.fromHex(key),
        ciphertext = Array.fromHex(data),
        padding = ZeroPadding
    }
    
    local decipher = assert(chiperData.decipher()
            .setKey(chiperData.key)
            .setBlockCipher(AES256Cipher)
            .setPadding(chiperData.padding));

    local plainOutput = assert(decipher
                        .init()
                        .update(Stream.fromArray(chiperData.iv))
                        .update(Stream.fromArray(chiperData.ciphertext))
                        .finish()
                        .asHex(), "nepavyko issifruoti");

    local result = string.fromhex(plainOutput)
    return string.match(result, "(.+)%;(.+)")
end

function crypto.decryptPayload(payload, key)
    local parsed_payload = json.decode(payload)
    local data = {
        iv = parsed_payload.iv,
        data = parsed_payload.data
    }

    print(data.iv)
    print("data: " .. data.data)
    print("Key: " .. key)

    local result = assert(crypto.decrypt(data.iv, key, data.data))
    return result
end

function crypto.loadKey(keyPath)
    --uzkraunam rakto hex
    local key_file = io.open(keyPath,"rb")
    local key = key_file:read()
    --print(key)
    key_file:close()
    return key
end

return crypto