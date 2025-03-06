#include <iostream>
#include <cstdlib>
#include <array>
#include <chrono>
#include <thread>

#include <RadioLib.h>
#include "hal/RPi/PiHal.h"
#include <lgpio.h>
#include <sqlite3.h>

constexpr uint32_t uplinkIntervalSeconds = 20UL * 60UL;

constexpr uint64_t joinEui = 0x0000000000000000;
constexpr uint64_t devEui  = 0x70B3D57ED006E3C0;

constexpr std::array<uint8_t, 16> appKey = {
	0x6C, 0x96, 0xB9, 0x45, 0xCB, 0x55, 0x88, 0x99, 0x3A, 0xCD, 0xF2, 0xC4, 0xE6, 0x3F, 0x32, 0x69
};
constexpr std::array<uint8_t, 16> nwkKey = {
	0xEE, 0xCA, 0x78, 0x49, 0x33, 0x23, 0xA5, 0x21, 0x29, 0x28, 0xB0, 0x10, 0xA7, 0x20, 0x16, 0x46
};

constexpr size_t maxPayloadSize = 10;

//constexpr uint32_t deviceAddress = 0x260BB29A;
//constexpr std::array<uint8_t, 16> appSKey = {
	//0x53, 0xF3, 0xDD, 0xA2, 0x8F, 0x81, 0x8D, 0x5B, 0x3B, 0x08, 0xFF, 0xA9, 0x9A, 0xCB, 0x83, 0xE6
//};
//constexpr std::array<uint8_t, 16> fNwkSIntKey = {
	//0x87, 0xCF, 0xE9, 0x37, 0xF5, 0x16, 0x9E, 0xC4, 0xA6, 0xC1, 0x6C, 0x6A, 0xAD, 0x0C, 0x55, 0xF9
//};
//constexpr std::array<uint8_t, 16> SNwkSIntKey = {
	//0xEE, 0x23, 0xCD, 0x10, 0x99, 0xC5, 0xE0, 0x37, 0x48, 0xE8, 0xE7, 0x95, 0x33, 0xF9, 0xFC, 0x5B
//};
//constexpr std::array<uint8_t, 16> nwkSEncKey = {
	//0xEC, 0x9A, 0x63, 0xC1, 0x8B, 0xA4, 0x89, 0x26, 0x3E, 0xF7, 0x80, 0xB6, 0xD6, 0xF5, 0x91, 0xFE
//};

PiHal* hal = new PiHal(0);
SX1262 radio = new Module(hal, 21, 16, 18, 20);

LoRaWANBand_t region = EU868;
uint8_t subBand = 0;

LoRaWANNode node(&radio, &region, subBand);

int main(int argc, char** argv) {
	std::cout << "Waiting a minute to order services" << std::endl;
  
  	std::this_thread::sleep_for(std::chrono::milliseconds(60 * 1000UL));

	std::cout << "[SX1262] Initializing radio ... ";
  	
	radio.XTAL = true;
	radio.setTCXO(0.0);
	int state = radio.begin();
  	if (state != RADIOLIB_ERR_NONE) {
		std::cout << "failed, code " << state << std::endl;
    	return EXIT_FAILURE;
  	}
	std::cout << "success!" << std::endl;

	std::cout << "[SX1262] Begin OTAA ... ";
	state = node.beginOTAA(joinEui, devEui, nwkKey.data(), appKey.data());
	//state = node.beginABP(deviceAddress, fNwkSIntKey.data(), SNwkSIntKey.data(), nwkSEncKey.data(), appSKey.data());
	if (state != RADIOLIB_ERR_NONE) {
		std::cout << "failed, code " << state << std::endl;
    	return EXIT_FAILURE;
	}
	std::cout << "success!" << std::endl;

	std::cout << "[SX1262] Activate OTAA ... ";
	state = node.activateOTAA();
	//state = node.activateABP();
	if (state != RADIOLIB_LORAWAN_NEW_SESSION) {
		std::cout << "failed, code " << state << std::endl;
    	return EXIT_FAILURE;
	}
	std::cout << "success!" << std::endl;

	std::cout << "[SX1262] Ready" << std::endl;

  	while (true) {
		std::cout << "Getting most recent payload from DB..." << std::endl;

		struct sqlite3* sqliteHandle = nullptr;
		if (sqlite3_open("/var/local/sensor_data.db", &sqliteHandle) != SQLITE_OK) {
			std::cerr << "Unable to open database sensor_data" << std::endl;
			continue;
		}
		std::cout << "Opened connection to DB" << std::endl;

		sqlite3_stmt* selectPayloadStatement;
		std::string selectPayload = "SELECT payload "
			                        "FROM sensor_data "
			                        "WHERE id = (SELECT MAX(id) FROM sensor_data)";

		std::array<uint8_t, maxPayloadSize> extractedPayload {};
		if (sqlite3_prepare_v2(sqliteHandle, selectPayload.data(), -1, &selectPayloadStatement, 0) == SQLITE_OK) {
			while (sqlite3_step(selectPayloadStatement) == SQLITE_ROW) {
				// Get the binary data
				const void* data = sqlite3_column_blob(selectPayloadStatement, 0);
				int dataSize = sqlite3_column_bytes(selectPayloadStatement, 0);
		
				// Print the binary data to check correctness
				std::cout << "Retrieved binary data: ";
				for (int i = 0; i < maxPayloadSize; i++) {
					printf("%02X ", ((unsigned char*)data)[i]);
					extractedPayload[i] = ((uint8_t*)(data))[i];
				}
				std::cout << std::endl;
			}
		}
		sqlite3_finalize(selectPayloadStatement);

		sqlite3_close(sqliteHandle);
		std::cout << "Closed connection to DB" << std::endl;

    	std::cout << "[SX1262] Transmitting packet ... " << std::endl;
		
		//std::this_thread::sleep_for(std::chrono::milliseconds(2000UL));
		//continue; // development purposes to avoid saturating LoRaWAN network for each restart of the program
  
  		state = node.sendReceive(extractedPayload.data(), extractedPayload.size());    
		if (state < RADIOLIB_ERR_NONE) {
			std::cout << "failed, code " << state << std::endl;
		}

  		if(state > 0) {
    		std::cout << "Received a downlink" << std::endl;
  		} else {
    		std::cout << "No downlink received" << std::endl;
  		}

  		std::cout << "Next uplink in " << uplinkIntervalSeconds << " seconds" << std::endl;
  
  		std::this_thread::sleep_for(std::chrono::milliseconds(uplinkIntervalSeconds * 1000UL));
  	}

	delete hal;

  	return EXIT_SUCCESS;
}
