<DTIG_IMPORTS>
#include <RTI/LogicalTimeInterval.h>
#include <RTI/RTI1516fedTime.h>
#include <RTI/RTIambassador.h>
#include <RTI/RTIambassadorFactory.h>

#include <algorithm>
#include <locale>
#include <codecvt>
#include <memory>

#include <chrono>
#include <fstream>
#include <string>
#include <thread>

#include "DTIG>AMBASSADOR_HEADER"

#include "dtig/dt_message.pb.h"
#include "dtig/initialize.pb.h"
#include "dtig/return_code.pb.h"
#include "dtig/advance.pb.h"
#include "dtig/start.pb.h"
#include "dtig/stop.pb.h"
#include "dtig/state.pb.h"
#include "dtig/output.pb.h"
#include "dtig/get_status.pb.h"
#include "dtig/set_parameter.pb.h"
#include "dtig/get_parameter.pb.h"

#define MSG_SIZE 1024

using namespace std;
using namespace rti1516;

static const double STEP = DTIG_STEP_SIZE;
static const double STOP_TIME = DTIG_STOP_TIME;

DTIG_DEF DTIG_READ_STRING(TYPE, NAME, ITEM)
DTIG_IF(DTIG>ITEM == 0)
    if (item == DTIG_STR(DTIG>TYPE))
DTIG_ELSE
    else if (item == DTIG_STR(DTIG>TYPE))
DTIG_END_IF
DTIG_IF(DTIG>TYPE == DTIG>NAME)
DTIG_IF(DTIG_TO_TYPE(DTIG>TYPE) == DTIG_TO_TYPE(DTIG_TYPE_STRING))
      anyValue.mutable_DTIG>TYPE()->set_value(fromData(it->second));
DTIG_ELSE
      anyValue.mutable_DTIG>TYPE()->set_value(fromData<DTIG_TO_TYPE(DTIG>TYPE)>(it->second));
DTIG_END_IF
DTIG_ELSE
DTIG_IF(DTIG_TO_TYPE(DTIG>TYPE) == DTIG_TO_TYPE(DTIG_TYPE_STRING))
      anyValue.set_value(it->second);
DTIG_ELSE
      anyValue.set_value(fromData<DTIG_TO_TYPE(DTIG>NAME)>(it->second));
DTIG_END_IF
DTIG_END_IF
DTIG_END_DEF

DTIG_DEF DTIG_READ_FROM_DATA (TYPE, PREFIX)
DTIG_IF(DTIG>TYPE == DTIG_TYPE_PROP_VALUE)
DTIG_READ_STRING(DTIG>TYPE, DTIG_ITEM_TYPE, DTIG>PREFIX)
DTIG_ELSE
DTIG_READ_STRING(DTIG>TYPE, DTIG>TYPE, DTIG>PREFIX)
DTIG_END_IF
DTIG_END_DEF

DTIG_DEF DTIG_WRITE_STRING(TYPE, NAME, PREFIX)
DTIG_IF(DTIG>TYPE == DTIG>NAME)
  DTIG_TO_TYPE(DTIG>NAME) tmpDTIG>TYPE = message.DTIG>TYPE().value();
  DTIG_IF(DTIG_TO_TYPE(DTIG>TYPE) == DTIG_TO_TYPE(DTIG_TYPE_STRING))
  toWrite[mDTIG>PREFIXDTIG_ITEM_NAME.at(DTIG_STR(DTIG>TYPE))] = toData(&tmpDTIG>TYPE);
  DTIG_ELSE
  toWrite[mDTIG>PREFIXDTIG_ITEM_NAME.at(DTIG_STR(DTIG>TYPE))] = toData<DTIG_TO_TYPE(DTIG>NAME)>(&tmpDTIG>TYPE);
  DTIG_END_IF
DTIG_ELSE
  DTIG_TO_TYPE(DTIG>NAME) tmpDTIG>TYPE = message.DTIG>TYPE();
  DTIG_IF(DTIG_TO_TYPE(DTIG>TYPE) == DTIG_TO_TYPE(DTIG_TYPE_STRING))
  toWrite[mDTIG>PREFIXDTIG_ITEM_NAME.at(DTIG_STR(DTIG>TYPE))] = toData(&tmpDTIG>TYPE);
  DTIG_ELSE
  toWrite[mDTIG>PREFIXDTIG_ITEM_NAME.at(DTIG_STR(DTIG>TYPE))] = toData<DTIG_TO_TYPE(DTIG>NAME)>(&tmpDTIG>TYPE);
  DTIG_END_IF
DTIG_END_IF
DTIG_END_DEF

DTIG_DEF DTIG_WRITE_TO_DATA (TYPE, PREFIX)
DTIG_IF(DTIG>TYPE == DTIG_TYPE_PROP_VALUE)
DTIG_WRITE_STRING(DTIG>TYPE, DTIG_ITEM_TYPE, DTIG>PREFIX)
DTIG_ELSE
DTIG_WRITE_STRING(DTIG>TYPE, DTIG>TYPE, DTIG>PREFIX)
DTIG_END_IF
DTIG_END_DEF

<DTIG_CLASSNAME>
HLAFederate

<DTIG_CONSTRUCTOR(PUBLIC)>
HLAFederate()
{
}

<DTIG_DESTRUCTOR(PUBLIC)>
~HLAFederate()
{
  if (mClient >= 0)
    close(mClient);
}

<DTIG_METHOD(PRIVATE)>
std::wstring convertStringToWstring(const std::string& str)
{
  const std::ctype<wchar_t>& CType = std::use_facet<std::ctype<wchar_t> >(std::locale());
  std::vector<wchar_t> wideStringBuffer(str.length());
  CType.widen(str.data(), str.data() + str.length(), &wideStringBuffer[0]);
  return std::wstring(&wideStringBuffer[0], wideStringBuffer.size());
}

<DTIG_CALLBACK(RUNCLIENT)>
bool RunModel()
{
  // Publish all parameters on start up
  DTIG>CALLBACK(GET_PARAMETER)();

  dtig::MReturnValue ret;

  dtig::MGetStatus statusValue;
  dtig::MDTMessage statusMessage;
  statusValue.set_request(true);
  *statusMessage.mutable_get_status() = statusValue;

DTIG_IF(DTIG_FORMALISM == DTIG_FORMALISM_FEM)
  // Running with a FEM model
  dtig::MStart startvalue;
  startvalue.mutable_start_time()->set_value(0.0f);
  startvalue.mutable_stop_time()->set_value(STOP_TIME);
  startvalue.mutable_step_size()->set_step(STEP);
  startvalue.set_run_mode(dtig::Run::CONTINUOUS);

  dtig::MDTMessage startMessage;
  *startMessage.mutable_start() = startvalue;

  while (fedamb->federateTime < STOP_TIME)
  {
    // If not stepped, just send start
    ret = SendMessage(startMessage);
    if (ret.code() != dtig::ReturnCode::SUCCESS)
    {
      std::cout << "Stopped: " << ret.error_message().value() << std::endl;
      return false;
    }

    do
    {
      // Wait until model is ready
      ret = SendMessage(statusMessage);
      if (ret.has_status() && ret.status().state() == dtig::State::EState::RUNNING)
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
      else
        break;
    } while (true);

    DTIG>CALLBACK(GET_OUTPUT)();

    startMessage.mutable_start()->mutable_start_time()->set_value(
      startMessage.mutable_start()->start_time().value() + STEP);
    startMessage.mutable_start()->mutable_stop_time()->set_value(
      startMessage.mutable_start()->start_time().value() + STEP);

    advanceTime(STEP);
    std::cout << "Time Advanced to " << fedamb->federateTime << std::endl;
  }

DTIG_ELSE_IF(DTIG_FORMALISM == DTIG_FORMALISM_CONTINUOUS)
  // Running with a continuous model
  dtig::MStart startvalue;
  startvalue.mutable_start_time()->set_value(0.0f);
  startvalue.mutable_stop_time()->set_value(STOP_TIME);
  startvalue.mutable_step_size()->set_step(STEP);
  startvalue.set_run_mode(dtig::Run::STEPPED);

  dtig::MAdvance advanceValue;
  advanceValue.mutable_step_size()->set_step(STEP);

  dtig::MDTMessage startMessage;
  *startMessage.mutable_start() = startvalue;

  dtig::MDTMessage advanceMessage;
  *advanceMessage.mutable_advance() = advanceValue;

  // Start the model
  ret = SendMessage(startMessage);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Stopped: " << ret.error_message().value() << std::endl;
    return false;
  }

  std::cout << "Waiting for model to start" << std::endl;
  do
  {
    ret = SendMessage(statusMessage);
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
  } while (ret.has_status() &&
           ret.status().state() != dtig::State::EState::INITIALIZED &&
           ret.status().state() != dtig::State::EState::RUNNING &&
           ret.status().state() != dtig::State::EState::WAITING &&
           ret.status().state() != dtig::State::EState::STOPPED);


  while (fedamb->federateTime < STOP_TIME)
  {
    ret = SendMessage(advanceMessage);
    if (ret.code() != dtig::ReturnCode::SUCCESS)
    {
      std::cout << "Stopped: " << ret.error_message().value() << std::endl;
      break;
    }

    do
    {
      // Wait until outputs are ready
      ret = SendMessage(statusMessage);
      if (ret.has_status() && ret.status().state() == dtig::State::EState::RUNNING)
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
      else
        break;
    } while (true);

    // std::cout << "Current status: " << dtig::State::EState_Name(ret.status().state()) << std::endl;
    DTIG>CALLBACK(GET_OUTPUT)();

    advanceTime(STEP);
    std::cout << "Time Advanced to " << fedamb->federateTime << std::endl;
  }
DTIG_ELSE_IF(DTIG_FORMALISM == DTIG_FORMALISM_DISCRETE)
  // Running with a discrete model
  dtig::MStart startvalue;
  startvalue.mutable_start_time()->set_value(0.0f);
  startvalue.mutable_stop_time()->set_value(STOP_TIME);
  startvalue.mutable_step_size()->set_step(STEP);
  startvalue.set_run_mode(dtig::Run::CONTINUOUS);

  dtig::MDTMessage startMessage;
  *startMessage.mutable_start() = startvalue;

  while (fedamb->federateTime < STOP_TIME)
  {
    advanceTime(STEP);
    std::cout << "Time Advanced to " << fedamb->federateTime << std::endl;
  }
DTIG_END_IF

  return true;
}

<DTIG_RUN>
void runFederate(const std::string& federateName, const std::string& fom, const std::string& address, uint32_t port)
{
  rti1516::RTIambassadorFactory* factory = new rti1516::RTIambassadorFactory();
  std::vector<std::wstring> args;
  args.push_back(L"protocol=rti");
  args.push_back(L"address=" + convertStringToWstring(address));

  rtiamb = factory->createRTIambassador(args);

  try
  {
    rtiamb->createFederationExecution(L"ExampleFederation", convertStringToWstring(fom));
    std::cout << "Created Federation" << std::endl;
  }
  catch (FederationExecutionAlreadyExists exists)
  {
    std::cout << "Didn't create federation, it already existed" << std::endl;
  }
  catch (ErrorReadingFDD error)
  {
    std::wcout << error.what() << std::endl;
    return;
  }

  fedamb = std::make_shared<DTIG>AMBASSADOR>();

  mName = federateName;

  rtiamb->joinFederationExecution(convertStringToWstring(federateName), convertStringToWstring("ExampleFederation"), *fedamb);
  std::cout << "Joined Federation as " << federateName << std::endl;

  if ((mClient = socket(AF_INET, SOCK_STREAM, 0)) < 0)
  {
    std::cout << "Socket creation error" << std::endl;
    return;
  }

  mPort = port;
  struct sockaddr_in serv_addr;
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(port);

  // Convert IPv4 and IPv6 addresses from text to binary form
  if (inet_pton(AF_INET, address.c_str(), &serv_addr.sin_addr) <= 0)
  {
    std::cout << "Invalid address/ Address not supported" << std::endl;
    return;
  }

  std::cout << "Connection to common server at " << address << ":" << port << std::endl;
  if (connect(mClient, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0)
  {
    std::cout << "Connection Failed" << std::endl;
    return;
  }


  dtig::MDTMessage message;
  dtig::MInitialize initializeMessage;
  initializeMessage.mutable_model_name()->set_value(DTIG_STR(DTIG_MODEL_PATH));
  *message.mutable_initialize() = initializeMessage;

  auto initRet = SendMessage(message);
  if (initRet.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to initialize: " << initRet.error_message().value() << std::endl;
    return;
  }

  DTIG>CALLBACK(INITIALIZE)();

  rtiamb->registerFederationSynchronizationPoint(convertStringToWstring(READY_TO_RUN), toVariableLengthData(""));
  std::cout << "SynchronizationPoint registered" << std::endl;
  while (fedamb->isAnnounced == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  std::cout << "Initialized model. Continue?" << std::endl;
  waitForUser();

  rtiamb->synchronizationPointAchieved(convertStringToWstring(READY_TO_RUN));
  std::cout << "Achieved sync point: " << READY_TO_RUN << ", waiting for federation..." << std::endl;
  while (fedamb->isReadyToRun == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  enableTimePolicy();
  std::cout << "Time Policy Enabled" << std::endl;

  publishAndSubscribe();
  std::cout << "Published and Subscribed" << std::endl;

  std::cout << "Starting loop" << std::endl;
  DTIG>CALLBACK(RUNCLIENT)();

  std::cout << "Simulation done: " << fedamb->federateTime << std::endl;
  waitForUser();

  dtig::MDTMessage dtMessage;
  dtig::MStop stopMessage;
  stopMessage.set_mode(dtig::Stop::CLEAN);
  *dtMessage.mutable_stop() = stopMessage;

  auto stopRet = SendMessage(dtMessage);
  if (stopRet.code() != dtig::ReturnCode::SUCCESS)
    std::cout << "Failed to start: " << stopRet.error_message().value() << std::endl;

  rtiamb->resignFederationExecution(NO_ACTION);
  std::cout << "Resigned from Federation" << std::endl;

  try
  {
    rtiamb->destroyFederationExecution(L"ExampleFederation");
    std::cout << "Destroyed Federation" << std::endl;
  }
  catch (FederationExecutionDoesNotExist dne)
  {
    std::cout << "No need to destroy federation, it doesn't exist" << std::endl;
  }
  catch (FederatesCurrentlyJoined fcj)
  {
    std::cout << "Didn't destroy federation, federates still joined" << std::endl;
  }
}

<DTIG_METHOD(PRIVATE)>
void waitForUser()
{
  std::cout << ">>>>>>>>>> Press Enter to Continue <<<<<<<<<<" << std::endl;
  (void)getchar();
}

<DTIG_METHOD(PRIVATE)>
void enableTimePolicy()
{
  HLAfloat64Interval lookahead(fedamb->federateLookahead);
  rtiamb->enableTimeRegulation(lookahead);

  // wait for callback
  while (fedamb->isRegulating == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  rtiamb->enableTimeConstrained();

  // wait for callback
  while (fedamb->isConstrained == false)
  {
    rtiamb->evokeCallback(12.0);
  }
}

<DTIG_METHOD(PRIVATE)>
void publishAndSubscribe()
{
  fedamb->interactionReceived = [this](rti1516::InteractionClassHandle theInteraction, const rti1516::ParameterHandleValueMap& theParameterValues) {
    InteractionReceived(theInteraction, theParameterValues);
  };

  DTIG>CALLBACK(SUBSCRIBE)();
  DTIG>CALLBACK(PUBLISH)();
}

<DTIG_METHOD(PRIVATE)>
rti1516::VariableLengthData toVariableLengthData(const char* s)
{
  return toData(s);
}

<DTIG_METHOD(PRIVATE)>
void advanceTime(double timestep)
{
  /// request the advance
  fedamb->isAdvancing = true;
  RTI1516fedTime newTime = (fedamb->federateTime + timestep);
  rtiamb->timeAdvanceRequest(newTime);

  /// wait for the time advance to be granted. ticking will tell the
  /// LRC to start delivering callbacks to the federate
  while (fedamb->isAdvancing)
  {
    rtiamb->evokeCallback(12.0);
  }
}

<DTIG_METHOD(PRIVATE)>
dtig::MReturnValue SendMessage(const google::protobuf::Message& message)
{
  dtig::MReturnValue result;

  auto toSend = message.SerializeAsString();
  send(mClient, toSend.c_str(), toSend.size(), 0);

  auto bytesRead = read(mClient, mBuffer, MSG_SIZE - 1);
  if (bytesRead <= 0)
  {
    result.set_code(dtig::ReturnCode::INVALID_STATE);
    result.mutable_error_message()->set_value("Server disconnected");
    return result;
  }

  if (!result.ParseFromArray(mBuffer, bytesRead))
  {
    result.set_code(dtig::ReturnCode::FAILURE);
    result.mutable_error_message()->set_value("Failed to parse response");
    return result;
  }

  return result;
}

<DTIG_METHOD(PRIVATE)>
void InteractionReceived(rti1516::InteractionClassHandle interaction, const rti1516::ParameterHandleValueMap& values)
{
DTIG_IF(NOT DTIG_INPUTS AND NOT DTIG_PARAMETERS)
  return;
DTIG_ELSE
  DTIG_FOR(DTIG_INPUTS)
  DTIG_IF(DTIG_INDEX == 0)
  if (interaction == mIDTIG_ITEM_NAME)
  DTIG_ELSE
  else if (interaction == mIDTIG_ITEM_NAME)
  DTIG_END_IF
    SetInputDTIG_ITEM_NAME(values);
  DTIG_END_FOR
  DTIG_FOR(DTIG_PARAMETERS)
  DTIG_IF(DTIG_INDEX == 0 AND NOT DTIG_INPUTS)
  if (interaction == mPDTIG_ITEM_NAME)
  DTIG_ELSE
  else if (interaction == mPDTIG_ITEM_NAME)
  DTIG_END_IF
    SetParameterDTIG_ITEM_NAME(values);
  DTIG_END_FOR
DTIG_END_IF
}

<DTIG_CALLBACK(INITIALIZE)>
// ===================================================
// INITIALIZE callback
void initializeHandles()
{
  // Parameters
  DTIG_FOR(DTIG_PARAMETERS)
  try
  {
    mPDTIG_ITEM_NAME = rtiamb->getInteractionClassHandle(L"DTIG_ITEM_NAMESPACE.DTIG_ITEM_NAME");
    DTIG_IF(DTIG_ITEM_TYPE == DTIG_TYPE_FORCE OR DTIG_ITEM_TYPE == DTIG_TYPE_FIXTURE)
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_MAGNITUDE), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_MAGNITUDE")});
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_OBJECT), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_OBJECT")});
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_REFERENCE), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_REFERENCE")});
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_DIRECTION), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_DIRECTION")});
    DTIG_ELSE_IF(DTIG_ITEM_TYPE == DTIG_TYPE_MATERIAL)
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_STATE), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_STATE")});
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_NAME), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_NAME")});
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_YOUNGS_MODULUS), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_YOUNGS_MODULUS")});
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_POISSON_RATIO), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_POISSON_RATIO")});
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_DENSITY), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_DENSITY")});
    DTIG_ELSE
    mPsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_VALUE), rtiamb->getParameterHandle(mPDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_VALUE")});
    DTIG_END_IF
  }
  catch (rti1516::NameNotFound e)
  {
    std::wcout << "Failed to initialize parameter handle DTIG_ITEM_NAME" << e.what() << std::endl;
    return;
  }
  DTIG_END_FOR

  // Inputs
  DTIG_FOR(DTIG_INPUTS)
  try
  {
    mIDTIG_ITEM_NAME = rtiamb->getInteractionClassHandle(L"DTIG_ITEM_NAMESPACE.DTIG_ITEM_NAME");
    DTIG_IF(DTIG_ITEM_TYPE == DTIG_TYPE_FORCE OR DTIG_ITEM_TYPE == DTIG_TYPE_FIXTURE)
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_MAGNITUDE"), DTIG_STR(DTIG_TYPE_PROP_MAGNITUDE)});
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_OBJECT"), DTIG_STR(DTIG_TYPE_PROP_OBJECT)});
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_REFERENCE"), DTIG_STR(DTIG_TYPE_PROP_REFERENCE)});
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_DIRECTION"), DTIG_STR(DTIG_TYPE_PROP_DIRECTION)});
    DTIG_ELSE_IF(DTIG_ITEM_TYPE == DTIG_TYPE_MATERIAL)
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_STATE"), DTIG_STR(DTIG_TYPE_PROP_STATE)});
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_NAME"), DTIG_STR(DTIG_TYPE_PROP_NAME)});
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_YOUNGS_MODULUS"), DTIG_STR(DTIG_TYPE_PROP_YOUNGS_MODULUS)});
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_POISSON_RATIO"), DTIG_STR(DTIG_TYPE_PROP_POISSON_RATIO)});
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_DENSITY"), DTIG_STR(DTIG_TYPE_PROP_DENSITY)});
    DTIG_ELSE
    mIsDTIG_ITEM_NAME.insert({rtiamb->getParameterHandle(mIDTIG_ITEM_NAME, L"DTIG_TYPE_PROP_VALUE"), DTIG_STR(DTIG_TYPE_PROP_VALUE)});
    DTIG_END_IF
  }
  catch (rti1516::NameNotFound e)
  {
    std::wcout << "Failed to initialize input handle DTIG_ITEM_NAME:" << e.what() << std::endl;
    return;
  }
  DTIG_END_FOR

  // Outputs
  DTIG_FOR(DTIG_OUTPUTS)
  try
  {
    mODTIG_ITEM_NAME = rtiamb->getInteractionClassHandle(L"DTIG_ITEM_NAMESPACE.DTIG_ITEM_NAME");
    DTIG_IF(DTIG_ITEM_TYPE == DTIG_TYPE_FORCE OR DTIG_ITEM_TYPE == DTIG_TYPE_FIXTURE)
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_MAGNITUDE), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_MAGNITUDE")});
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_OBJECT), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_OBJECT")});
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_REFERENCE), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_REFERENCE")});
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_DIRECTION), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_DIRECTION")});
    DTIG_ELSE_IF(DTIG_ITEM_TYPE == DTIG_TYPE_MATERIAL)
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_STATE), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_STATE")});
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_NAME), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_NAME")});
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_YOUNGS_MODULUS), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_YOUNGS_MODULUS")});
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_POISSON_RATIO), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_POISSON_RATIO")});
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_DENSITY), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_DENSITY")});
    DTIG_ELSE
    mOsDTIG_ITEM_NAME.insert({DTIG_STR(DTIG_TYPE_PROP_VALUE), rtiamb->getParameterHandle(mODTIG_ITEM_NAME, L"DTIG_TYPE_PROP_VALUE")});
    DTIG_END_IF
  }
  catch (rti1516::NameNotFound e)
  {
    std::wcout << "Failed to initialize output handle DTIG_ITEM_NAME:" << e.what() << std::endl;
    return;
  }
  DTIG_END_FOR
}

<DTIG_CALLBACK(SET_INPUT)>
// ===================================================
// SET_INPUT callback
void SetInputs(const rti1516::InteractionClassHandle& interaction, const rti1516::ParameterHandleValueMap& parameterValues)
{
  return;
}

DTIG_IF(DTIG_FORMALISM == DTIG_FORMALISM_DISCRETE)
void DTIG>CLASSNAME::DiscreteTimeAdvance()
{
  dtig::MStart startvalue;
  startvalue.mutable_start_time()->set_value(0.0f);
  startvalue.mutable_stop_time()->set_value(STOP_TIME);
  startvalue.mutable_step_size()->set_step(STEP);
  startvalue.set_run_mode(dtig::Run::CONTINUOUS);

  dtig::MDTMessage startMessage;
  *startMessage.mutable_start() = startvalue;

  dtig::MGetStatus statusValue;
  dtig::MDTMessage statusMessage;
  statusValue.set_request(true);
  *statusMessage.mutable_get_status() = statusValue;

  auto ret = SendMessage(startMessage);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Stopped: " << ret.error_message().value() << std::endl;
    return;
  }

  do
  {
    // Wait until model is ready
    ret = SendMessage(statusMessage);
    if (ret.has_status() && ret.status().state() == dtig::State::EState::RUNNING)
      std::this_thread::sleep_for(std::chrono::milliseconds(5));
    else
      break;
  } while (true);

  DTIG>CALLBACK(GET_OUTPUT)();
}
DTIG_END_IF

DTIG_FOR(DTIG_INPUTS)
// Set the input DTIG_ITEM_NAME:
void DTIG>CLASSNAME::SetInputDTIG_ITEM_NAME(const rti1516::ParameterHandleValueMap& handles)
{
  std::unique_lock<std::mutex> lock(mMutex);
  DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) anyValue;
  for (auto it = handles.begin(); it != handles.end(); ++it)
  {
    std::string item = mIsDTIG_ITEM_NAME[it->first];
    DTIG_IF(DTIG_ITEM_TYPE == DTIG_TYPE_FORCE OR DTIG_ITEM_TYPE == DTIG_TYPE_FIXTURE)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_MAGNITUDE, 0)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_OBJECT,    1)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_REFERENCE, 2)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_DIRECTION, 3)
    DTIG_ELSE_IF(DTIG_ITEM_TYPE == DTIG_TYPE_MATERIAL)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_STATE,          0)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_NAME,           1)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_YOUNGS_MODULUS, 2)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_POISSON_RATIO,  3)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_DENSITY,        4)
    DTIG_ELSE
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_VALUE,          0)
    DTIG_END_IF
    else
      std::cout << "Unknown input handle (DTIG_ITEM_NAME): " << item << std::endl;
  }

  dtig::MInput inputMessage;
  *inputMessage.mutable_inputs()->add_identifiers() = DTIG_STR(DTIG_ITEM_NAME);
  inputMessage.mutable_inputs()->add_values()->PackFrom(anyValue);

  dtig::MDTMessage message;
  *message.mutable_set_input() = inputMessage;
  dtig::MReturnValue ret = SendMessage(message);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to set inputs: " << ret.error_message().value() << std::endl;
    return;
  }

  DTIG_IF(DTIG_FORMALISM == DTIG_FORMALISM_DISCRETE)
  DiscreteTimeAdvance();
  DTIG_END_IF
}
DTIG_END_FOR

<DTIG_CALLBACK(GET_OUTPUT)>
// ===================================================
// GET_OUTPUT callback
void GetOutput()
{
  DTIG_IF(NOT DTIG_OUTPUTS)
  return;
  DTIG_ELSE
  dtig::MOutput outputMessage;
  DTIG_FOR(DTIG_OUTPUTS)
  *outputMessage.mutable_outputs()->add_identifiers() = DTIG_STR(DTIG_ITEM_NAME);
  DTIG_END_FOR

  dtig::MDTMessage message;
  *message.mutable_get_output() = outputMessage;
  dtig::MReturnValue ret = SendMessage(message);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to get outputs: " << ret.error_message().value() << std::endl;
    return;
  }
  DTIG_FOR(DTIG_OUTPUTS)

  ParameterHandleValueMap paramDTIG_ITEM_NAME = OutputFromDTIG_ITEM_NAME(ret.values().values(DTIG_INDEX));
  rtiamb->sendInteraction(mODTIG_ITEM_NAME, paramDTIG_ITEM_NAME, toVariableLengthData(mName.c_str()));
  DTIG_END_FOR
  DTIG_END_IF
}

DTIG_FOR(DTIG_OUTPUTS)
// Update the output DTIG_ITEM_NAME:
rti1516::ParameterHandleValueMap DTIG>CLASSNAME::OutputFromDTIG_ITEM_NAME(const google::protobuf::Any& anyMessage)
{
  ParameterHandleValueMap toWrite;

  DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) message;
  if (!anyMessage.UnpackTo(&message))
  {
    std::cout << "Failed to unpack output: DTIG_ITEM_NAME" << std::endl;
    return toWrite;
  }

  DTIG_IF(DTIG_ITEM_TYPE == DTIG_TYPE_FORCE OR DTIG_ITEM_TYPE == DTIG_TYPE_FIXTURE)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_MAGNITUDE, Os)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_DIRECTION, Os)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_OBJECT, Os)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_REFERENCE, Os)
  DTIG_ELSE_IF(DTIG_ITEM_TYPE == DTIG_TYPE_MATERIAL)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_NAME, Os)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_STATE, Os)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_DENSITY, Os)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_YOUNGS_MODULUS, Os)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_POISSON_RATIO, Os)
  DTIG_ELSE
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_VALUE, Os)
  DTIG_END_IF

  return toWrite;
}
DTIG_END_FOR

<DTIG_CALLBACK(SET_PARAMETER)>
// ===================================================
// SET_PARAMETER callback
void SetParameters(const rti1516::InteractionClassHandle& handler, const rti1516::ParameterHandleValueMap& parameterValues)
{
  return;
}

DTIG_FOR(DTIG_PARAMETERS)
// Set the attribute (parameter) DTIG_ITEM_NAME:
void DTIG>CLASSNAME::SetParameterDTIG_ITEM_NAME(const rti1516::ParameterHandleValueMap& attributes)
{
  DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) anyValue;
  for (auto it = attributes.begin(); it != attributes.end(); ++it)
  {
    std::string item = GetHandleDTIG_ITEM_NAME(it->first);
    if (item.empty())
      continue;

    DTIG_IF(DTIG_ITEM_TYPE == DTIG_TYPE_FORCE OR DTIG_ITEM_TYPE == DTIG_TYPE_FIXTURE)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_MAGNITUDE, 0)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_OBJECT,    1)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_REFERENCE, 2)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_DIRECTION, 3)
    DTIG_ELSE_IF(DTIG_ITEM_TYPE == DTIG_TYPE_MATERIAL)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_STATE,          0)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_NAME,           1)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_YOUNGS_MODULUS, 2)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_POISSON_RATIO,  3)
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_DENSITY,        4)
    DTIG_ELSE
    DTIG_READ_FROM_DATA(DTIG_TYPE_PROP_VALUE,          0)
    DTIG_END_IF
    else
      std::cout << "Unknown handle: " << item << std::endl;
  }

  dtig::MSetParameter paramMessage;
  *paramMessage.mutable_parameters()->add_identifiers() = DTIG_STR(DTIG_ITEM_NAME);
  paramMessage.mutable_parameters()->add_values()->PackFrom(anyValue);

  dtig::MDTMessage message;
  *message.mutable_set_parameter() = paramMessage;
  dtig::MReturnValue ret = SendMessage(message);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
    std::cout << "Failed to set parameters: " << ret.error_message().value() << std::endl;
}

std::string DTIG>CLASSNAME::GetHandleDTIG_ITEM_NAME(const rti1516::ParameterHandle& handle) const
{
  for (auto it = mPsDTIG_ITEM_NAME.begin(); it != mPsDTIG_ITEM_NAME.end(); ++it)
    if (it->second == handle)
      return it->first;

  return std::string();
}
DTIG_END_FOR

<DTIG_CALLBACK(GET_PARAMETER)>
// ===================================================
// GET_PARAMETER callback
void GetParameter()
{
  DTIG_IF(NOT DTIG_PARAMETERS)
  return;
  DTIG_ELSE
  dtig::MGetParameter paramMessage;
  DTIG_FOR(DTIG_PARAMETERS)
  *paramMessage.mutable_parameters()->add_identifiers() = DTIG_STR(DTIG_ITEM_NAME);
  DTIG_END_FOR

  dtig::MDTMessage message;
  *message.mutable_get_parameter() = paramMessage;
  dtig::MReturnValue ret = SendMessage(message);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to get parameters: " << ret.error_message().value() << std::endl;
    return;
  }
  DTIG_FOR(DTIG_PARAMETERS)

  ParameterHandleValueMap paramDTIG_ITEM_NAME = ParameterFromDTIG_ITEM_NAME(ret.values().values(DTIG_INDEX));
  rtiamb->sendInteraction(mPDTIG_ITEM_NAME, paramDTIG_ITEM_NAME, toVariableLengthData(mName.c_str()));
  DTIG_END_FOR
  DTIG_END_IF
}

DTIG_FOR(DTIG_PARAMETERS)
rti1516::ParameterHandleValueMap DTIG>CLASSNAME::ParameterFromDTIG_ITEM_NAME(const google::protobuf::Any& anyMessage)
{
  ParameterHandleValueMap toWrite;

  DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) message;
  if (!anyMessage.UnpackTo(&message))
  {
    std::cout << "Failed to unpack output: DTIG_ITEM_NAME" << std::endl;
    return toWrite;
  }

  DTIG_IF(DTIG_ITEM_TYPE == DTIG_TYPE_FORCE OR DTIG_ITEM_TYPE == DTIG_TYPE_FIXTURE)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_MAGNITUDE, Ps)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_DIRECTION, Ps)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_OBJECT, Ps)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_REFERENCE, Ps)
  DTIG_ELSE_IF(DTIG_ITEM_TYPE == DTIG_TYPE_MATERIAL)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_NAME, Ps)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_STATE, Ps)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_DENSITY, Ps)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_YOUNGS_MODULUS, Ps)
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_POISSON_RATIO, Ps)
  DTIG_ELSE
  DTIG_WRITE_TO_DATA(DTIG_TYPE_PROP_VALUE, Ps)
  DTIG_END_IF

  return toWrite;
}
DTIG_END_FOR

<DTIG_CALLBACK(PUBLISH)>
// ===================================================
// PUBLISH callback
void SetupPublishers()
{
  // Define attributes (parameters) published by this class
  DTIG_FOR(DTIG_PARAMETERS)
  try
  {
    rtiamb->publishInteractionClass(mPDTIG_ITEM_NAME);
  }
  catch (rti1516::ObjectClassNotDefined e)
  {
    std::wcout << "Publish parameter class is not defined: DTIG_ITEM_NAME" << std::endl;
    return;
  }
  DTIG_END_FOR

  // Define outputs published by this class
  DTIG_FOR(DTIG_OUTPUTS)
  try
  {
    std::cout << "Setup publisher: DTIG_ITEM_NAME" << std::endl;
    rtiamb->publishInteractionClass(mODTIG_ITEM_NAME);
  }
  catch (rti1516::InteractionClassNotDefined e)
  {
    std::wcout << "Parameter class is not defined: DTIG_ITEM_NAME" << std::endl;
    return;
  }
  DTIG_END_FOR
}

<DTIG_CALLBACK(SUBSCRIBE)>
// ===================================================
// SUBSCRIBE callback
void SetupSubscribers()
{
  // Define attributes (parameters) to which this class subscribes
  DTIG_FOR(DTIG_PARAMETERS)
  try
  {
    rtiamb->subscribeInteractionClass(mPDTIG_ITEM_NAME);
  }
  catch (rti1516::ObjectClassNotDefined e)
  {
    std::wcout << "Publish parameter class is not defined: DTIG_ITEM_NAME" << std::endl;
    return;
  }
  DTIG_END_FOR
  // Define inputs to which this class subscribes
  DTIG_FOR(DTIG_INPUTS)
  try
  {
    std::cout << "Setup subscriber: DTIG_ITEM_NAME" << std::endl;
    rtiamb->subscribeInteractionClass(mIDTIG_ITEM_NAME);
  }
  catch (rti1516::InteractionClassNotDefined e)
  {
    std::wcout << "Input interaction class is not defined: DTIG_ITEM_NAME" << std::endl;
    return;
  }
  DTIG_END_FOR
}

<DTIG_MAIN>
#include <chrono>
#include <cstring>
#include <thread>

#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

int main(int argc, char *argv[])
{
  std::string federateName, fomPath, rtiAddress;
  std::string port;
  bool name = false;
  bool fom = false;
  bool address = false;

  for (int i = 0; i < argc; i++)
  {
    if (strcmp(argv[i], "--name") == 0)
    {
        federateName = argv[i + 1];
        name = true;
    }
    else if (strcmp(argv[i], "--fom") == 0)
    {
        fom = true;
        fomPath = argv[i + 1];
    }
    else if (strcmp(argv[i], "--host") == 0)
    {
        address = true;
        rtiAddress = argv[i + 1];
    }
    else if (strcmp(argv[i], "--port") == 0)
    {
      port = argv[i + 1];
    }
  }

  int child_status;
  pid_t childPid = 1; // fork();

  if (childPid > 0)
  {
    // Give some time for the server to start
    // std::this_thread::sleep_for(std::chrono::seconds(1));

    if (name && fom)
    {
      if (!address)
        rtiAddress = "127.0.0.1";

      // create and run the federate
      auto federate = std::make_shared<DTIG>CLASSNAME>();
      federate->DTIG>RUN(federateName, fomPath, rtiAddress, std::stoi(port));

      waitpid(childPid, 0, 0);
    }
    else
    {
      if (!name)
        std::cout << "No name given" << std::endl;
      if (!fom)
        std::cout << "No FOM location given" << std::endl;
    }
  }
  else
  {
    std::cout << "Fork failed" << std::endl;
    return -1;
  }

  return 0;
}