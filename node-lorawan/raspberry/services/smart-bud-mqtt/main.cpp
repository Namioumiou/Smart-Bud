#include <iostream>
#include <string>
#include <cstdlib>
#include <stdexcept>
#include <thread>
#include <chrono>

#include <mosquitto.h>
#include <sqlite3.h>

const std::string brokerAddr = "localhost";
const int brokerPort = 1883;
const std::string username = "test_un1";
const std::string password = "test_pwd1";
const std::string topic = "sensor_data";

std::string ToByte(char c) {
	std::string result = "";
	for (int i = 1; i <= 128; i *= 2) {
		result = ((c & i) ? "1" : "0") + result;
	}

	return result;
}

void OnMessage(struct mosquitto* mosq, void* obj, struct mosquitto_message const* message) {
	std::cout << "Received message on topic " << message->topic << std::endl;
	
	uint8_t* payload = static_cast<uint8_t*>(message->payload);

	std::string result_payload_binary {};
	std::string result_payload_ascii {};
	for (int i = 0; i < message->payloadlen; i++) {
		result_payload_binary += ToByte(payload[i]);
		result_payload_ascii += payload[i];
		std::cout << std::hex << int(payload[i]) << std::endl;
	}

	std::cout << "Resulting payload (in binary): " << result_payload_binary << std::endl;
	std::cout << "Resulting payload (in ASCII): " << result_payload_ascii << std::endl;

	struct sqlite3* sqliteHandle = nullptr;
	if (sqlite3_open("/var/local/sensor_data.db", &sqliteHandle) != SQLITE_OK) {
		std::cerr << "Unable to open database sensor_data" << std::endl;
		return;
	}

	std::cout << "Opened connection to DB" << std::endl;	

	std::string checkTableExistence = "CREATE TABLE IF NOT EXISTS sensor_data ("
		                              "id INTEGER PRIMARY KEY AUTOINCREMENT, "
		                              "topic TEXT NOT NULL, "
		                              "payload BLOB NOT NULL"
	                                  ");";
	//std::cout << checkTableExistence << std::endl;
	if (sqlite3_exec(sqliteHandle, checkTableExistence.c_str(), nullptr, nullptr, nullptr) != SQLITE_OK) {
		std::cerr << "An error occured while creating the sensor_data table" << std::endl;
		sqlite3_close(sqliteHandle);
		return;
	}

	std::cout << "Table created and/or opened" << std::endl;

	sqlite3_stmt* insertPayloadStatement = nullptr;
	std::string insertPayload = "INSERT INTO sensor_data (topic, payload) "
		                        "VALUES ('" + std::string(message->topic) + "', ?"
	                            ");";

	if (sqlite3_prepare_v2(sqliteHandle, insertPayload.data(), -1, &insertPayloadStatement, 0) != SQLITE_OK) {
        std::cerr << "Failed to prepare statement: " << sqlite3_errmsg(sqliteHandle) << std::endl;
		sqlite3_close(sqliteHandle);
        return;
    }

	std::cout << "Prepared statement for payload insertion" << std::endl;

	if (sqlite3_bind_blob(insertPayloadStatement, 1, message->payload, message->payloadlen, SQLITE_STATIC) != SQLITE_OK) {
        std::cerr << "Failed to bind blob: " << sqlite3_errmsg(sqliteHandle) << std::endl;
		sqlite3_finalize(insertPayloadStatement);
		sqlite3_close(sqliteHandle);
		return;
    }

	std::cout << "Payload binded to statement" << std::endl;

	if (sqlite3_step(insertPayloadStatement) != SQLITE_DONE) {
		std::cerr << "An error occured while inserting payload in the sensor_data table" << std::endl;
		std::cerr << "reason: " << sqlite3_errmsg(sqliteHandle) << std::endl;
		sqlite3_finalize(insertPayloadStatement);
		sqlite3_close(sqliteHandle);
		return;
	}

	std::cout << "Payload inserted" << std::endl;

	sqlite3_finalize(insertPayloadStatement);
	sqlite3_close(sqliteHandle);
	std::cout << "Closed connection to DB" << std::endl;
}
	
class MosquittoClient {
	public:
		MosquittoClient(std::string brokerAddr, int brokerPort, std::string username, std::string password);
		~MosquittoClient();

		bool Subscribe(std::string const& topic);
		bool Unsubscribe(std::string const& topic);

		void Loop();

	private:
		struct mosquitto* _mosquittoInstance = nullptr;
		std::string _brokerAddr = "";
		int _brokerPort = 0;
		std::string _username = "";
		std::string _password = "";
};

MosquittoClient::MosquittoClient(std::string brokerAddr, int brokerPort, std::string username, std::string password) {
	_brokerAddr = brokerAddr;
	_brokerPort = brokerPort;
	_username = username;
	_password = password;

	if (mosquitto_lib_init() != MOSQ_ERR_SUCCESS) {
		throw std::runtime_error("Unable to initialize the mosquitto library");
	}

	std::clog << "Mosquitto library initialized" << std::endl;

	_mosquittoInstance = mosquitto_new("sensors_data_receiver", false, nullptr);
	if (_mosquittoInstance == nullptr) {
		throw std::runtime_error("Unable to create a valid Mosquitto client instance");
	}

	std::clog << "Mosquitto instance created" << std::endl;

	mosquitto_message_callback_set(_mosquittoInstance, OnMessage);

	if (mosquitto_username_pw_set(_mosquittoInstance, _username.c_str(), _password.c_str()) != MOSQ_ERR_SUCCESS) {
		throw std::runtime_error("Either the credentials are invalid or there is no memory available");
	}

	std::clog << "Credentials set" << std::endl;

	if (mosquitto_connect(_mosquittoInstance, _brokerAddr.c_str(), _brokerPort, 15) != MOSQ_ERR_SUCCESS) {
		throw std::runtime_error("Unable to connect to broker");
	}

	std::clog << "Mosquitto client connected to broker at " << _brokerAddr << " on port " << _brokerPort << std::endl; 

	std::clog << "Mosquitto client instance ready" << std::endl;
}

MosquittoClient::~MosquittoClient() {
	mosquitto_disconnect(_mosquittoInstance);
	std::clog << "Disconnected from broker" << std::endl;

	mosquitto_destroy(_mosquittoInstance);
	std::clog << "Mosquitto instance destroyed" << std::endl;

	mosquitto_lib_cleanup();
	std::clog << "Mosquitto library cleaned up" << std::endl;

	std::clog << "Mosquitto client instance destroyed" << std::endl;
}

bool MosquittoClient::Subscribe(std::string const& topic) {
	if (mosquitto_subscribe(_mosquittoInstance, nullptr, topic.c_str(), 0) != MOSQ_ERR_SUCCESS) {
		std::cerr << "Unable to subscribe to topic " << topic << std::endl;
		return false;
	}

	return true;
}

bool MosquittoClient::Unsubscribe(std::string const& topic) {
	if (mosquitto_unsubscribe(_mosquittoInstance, nullptr, topic.c_str()) != MOSQ_ERR_SUCCESS) {
		std::cerr << "Unable to unsubscribe from topic " << topic << std::endl;
		return false;
	}

	return true;
}

void MosquittoClient::Loop() {
	mosquitto_loop_forever(_mosquittoInstance, -1, 1);
}

int main() {
	try {
		MosquittoClient client(brokerAddr, brokerPort, username, password);
	
		if (!client.Subscribe(topic)) {
			return EXIT_FAILURE;
		}

		std::clog << "Subscribed to topic " << topic << std::endl;
		
		client.Loop();
	}

	catch (std::runtime_error const& e) {
		std::cerr << "Unable to create a Mosquitto client" << std::endl;
		return EXIT_FAILURE;
	}

	return EXIT_SUCCESS;
}
