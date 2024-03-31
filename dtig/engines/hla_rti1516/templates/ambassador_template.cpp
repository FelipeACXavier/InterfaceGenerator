@imports
#include <RTI/RTI1516fedTime.h>
#include <string.h>

#include <locale>
#include <codecvt>
#include <iostream>
#include "logging.h"

using namespace rti1516;

@classname
HLAAmbassador

@constructor
HLAAmbassador()
{
  // initialize all the variable values
  federateTime = 0.0;
  federateLookahead = 1.0;

  isRegulating = false;
  isConstrained = false;
  isAdvancing = false;
  isAnnounced = false;
  isReadyToRun = false;
}

@destructor
~HLAAmbassador() throw()
{
}

@method
double convertTime(LogicalTime const& theTime)
{
  RTI1516fedTime castedTime = (RTI1516fedTime)theTime;
  return castedTime.getFedTime();
}

@method
void synchronizationPointRegistrationSucceeded(std::wstring const& label) throw(FederateInternalError)
{
  LOG_INFO("Successfully registered sync point: %ls", label.c_str());
}

@method
void synchronizationPointRegistrationFailed(std::wstring const& label, SynchronizationFailureReason reason) throw(FederateInternalError)
{
  LOG_INFO("Failed to register sync point: %ls", label.c_str());
}

@method
void announceSynchronizationPoint(std::wstring const& label, VariableLengthData const& theUserSuppliedTag) throw(FederateInternalError)
{
  LOG_INFO("Synchronization point announced: %ls", label.c_str());
  std::wstring compare = L"ReadyToRun";
  if (wcscmp(label.c_str(), compare.c_str()) == 0)
    this->isAnnounced = true;
}

@method
void federationSynchronized(std::wstring const& label) throw(FederateInternalError)
{
  LOG_INFO("Federation Synchronized: %ls", label.c_str());
  std::wstring compair = L"ReadyToRun";
  if (wcscmp(label.c_str(), compair.c_str()) == 0)
    this->isReadyToRun = true;
}

@method
void timeRegulationEnabled(LogicalTime const& theFederateTime) throw(InvalidLogicalTime,
                                                                                    NoRequestToEnableTimeRegulationWasPending,
                                                                                    FederateInternalError)
{
  this->isRegulating = true;
  this->federateTime = convertTime(theFederateTime);
}

@method
void timeConstrainedEnabled(LogicalTime const& theFederateTime) throw(InvalidLogicalTime,
                                                                                     NoRequestToEnableTimeConstrainedWasPending,
                                                                                     FederateInternalError)
{
  this->isConstrained = true;
  this->federateTime = convertTime(theFederateTime);
}

@method
void timeAdvanceGrant(LogicalTime const& theTime) throw(InvalidLogicalTime,
                                                        JoinedFederateIsNotInTimeAdvancingState,
                                                        FederateInternalError)
{
  this->isAdvancing = false;
  this->federateTime = convertTime(theTime);
}

@method
void discoverObjectInstance(ObjectInstanceHandle theObject,
                            ObjectClassHandle theObjectClass,
                            std::wstring const& theObjectInstanceName) throw(CouldNotDiscover,
                                                                             ObjectClassNotKnown,
                                                                             FederateInternalError)
{
  LOG_INFO("Discovered Object: handle= %ls, classHandle=%ls, name=%ls",
    theObject.toString().c_str(),
    theObjectClass.toString().c_str(),
    theObjectInstanceName.c_str());
}

@method
void reflectAttributeValues(ObjectInstanceHandle theObject,
                                           AttributeHandleValueMap const& theAttributeValues,
                                           VariableLengthData const& theUserSuppliedTag,
                                           OrderType sentOrder,
                                           TransportationType theType) throw(ObjectInstanceNotKnown,
                                                                             AttributeNotRecognized,
                                                                             AttributeNotSubscribed,
                                                                             FederateInternalError)
{
  LOG_INFO("Reflection Received: 1 %ls", theObject.toString().c_str());

  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;
  for (auto i = theAttributeValues.begin(); i != theAttributeValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("attrHandle=%s, attrValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
void reflectAttributeValues(ObjectInstanceHandle theObject,
                                           AttributeHandleValueMap const& theAttributeValues,
                                           VariableLengthData const& theUserSuppliedTag,
                                           OrderType sentOrder,
                                           TransportationType theType,
                                           RegionHandleSet const& theSentRegionHandleSet) throw(ObjectInstanceNotKnown,
                                                                                                AttributeNotRecognized,
                                                                                                AttributeNotSubscribed,
                                                                                                FederateInternalError)
{
  LOG_INFO("Reflection Received: 2 %ls", theObject.toString().c_str());

  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;
  for (auto i = theAttributeValues.begin(); i != theAttributeValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("attrHandle=%s, attrValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
void reflectAttributeValues(ObjectInstanceHandle theObject,
                                      AttributeHandleValueMap const& theAttributeValues,
                                      VariableLengthData const& theUserSuppliedTag,
                                      OrderType sentOrder,
                                      TransportationType theType,
                                      LogicalTime const& theTime,
                                      OrderType receivedOrder) throw(ObjectInstanceNotKnown,
                                                                     AttributeNotRecognized,
                                                                     AttributeNotSubscribed,
                                                                     FederateInternalError)
{
  LOG_INFO("Reflection Received: 3 %ls", theObject.toString().c_str());

  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;
  for (auto i = theAttributeValues.begin(); i != theAttributeValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("attrHandle=%s, attrValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
std::wstring variableLengthDataToWstring(const rti1516::VariableLengthData& variableLengthData)
{
  if (!variableLengthData.size())
    return std::wstring();
  return std::wstring((const wchar_t*)variableLengthData.data(),
                      variableLengthData.size() / sizeof(std::wstring::value_type));
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                                       ParameterHandleValueMap const& theParameterValues,
                                       VariableLengthData const& theUserSuppliedTag,
                                       OrderType sentOrder,
                                       TransportationType theType) throw(InteractionClassNotRecognized, InteractionParameterNotRecognized, InteractionClassNotSubscribed, FederateInternalError)
{
  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;

  auto interaction = converter.to_bytes(theInteraction.toString());
  std::string tag = std::string((char*)theUserSuppliedTag.data(), theUserSuppliedTag.size());

  LOG_INFO("Interaction 1 handle=%s, tag=%s, parameterCount=%u", interaction.c_str(), tag.c_str(), theParameterValues.size());

  for (auto i = theParameterValues.begin(); i != theParameterValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("paramHandle=%s, paramValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                                       ParameterHandleValueMap const& theParameterValues,
                                       VariableLengthData const& theUserSuppliedTag,
                                       OrderType sentOrder,
                                       TransportationType theType,
                                       RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized,
                                                                                            InteractionParameterNotRecognized,
                                                                                            InteractionClassNotSubscribed,
                                                                                            FederateInternalError)
{
  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;

  auto interaction = converter.to_bytes(theInteraction.toString());
  std::string tag = std::string((char*)theUserSuppliedTag.data(), theUserSuppliedTag.size());

  LOG_INFO("Interaction 2 handle=%s, tag=%s, parameterCount=%u", interaction.c_str(), tag.c_str(), theParameterValues.size());

  for (auto i = theParameterValues.begin(); i != theParameterValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("paramHandle=%s, paramValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                                       ParameterHandleValueMap const& theParameterValues,
                                       VariableLengthData const& theUserSuppliedTag,
                                       OrderType sentOrder,
                                       TransportationType theType,
                                       LogicalTime const& theTime,
                                       OrderType receivedOrder) throw(InteractionClassNotRecognized,
                                                                      InteractionParameterNotRecognized,
                                                                      InteractionClassNotSubscribed,
                                                                      FederateInternalError)
{
  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;

  auto interaction = converter.to_bytes(theInteraction.toString());
  std::string tag = std::string((char*)theUserSuppliedTag.data(), theUserSuppliedTag.size());

  LOG_INFO("Interaction 3 handle=%s, tag=%s, parameterCount=%u", interaction.c_str(), tag.c_str(), theParameterValues.size());

  for (auto i = theParameterValues.begin(); i != theParameterValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("paramHandle=%s, paramValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                                       ParameterHandleValueMap const& theParameterValues,
                                       VariableLengthData const& theUserSuppliedTag,
                                       OrderType sentOrder,
                                       TransportationType theType,
                                       LogicalTime const& theTime,
                                       OrderType receivedOrder,
                                       RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized,
                                                                                            InteractionParameterNotRecognized,
                                                                                            InteractionClassNotSubscribed,
                                                                                            FederateInternalError)
{
  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;

  auto interaction = converter.to_bytes(theInteraction.toString());
  std::string tag = std::string((char*)theUserSuppliedTag.data(), theUserSuppliedTag.size());

  LOG_INFO("Interaction 4 handle=%s, tag=%s, parameterCount=%u", interaction.c_str(), tag.c_str(), theParameterValues.size());

  for (auto i = theParameterValues.begin(); i != theParameterValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("paramHandle=%s, paramValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                                       ParameterHandleValueMap const& theParameterValues,
                                       VariableLengthData const& theUserSuppliedTag,
                                       OrderType sentOrder,
                                       TransportationType theType,
                                       LogicalTime const& theTime,
                                       OrderType receivedOrder,
                                       MessageRetractionHandle theHandle) throw(InteractionClassNotRecognized,
                                                                                InteractionParameterNotRecognized,
                                                                                InteractionClassNotSubscribed,
                                                                                InvalidLogicalTime,
                                                                                FederateInternalError)
{
  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;

  auto interaction = converter.to_bytes(theInteraction.toString());
  std::string tag = std::string((char*)theUserSuppliedTag.data(), theUserSuppliedTag.size());

  LOG_INFO("Interaction 5 handle=%s, tag=%s, parameterCount=%u", interaction.c_str(), tag.c_str(), theParameterValues.size());

  for (auto i = theParameterValues.begin(); i != theParameterValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("paramHandle=%s, paramValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                                       ParameterHandleValueMap const& theParameterValues,
                                       VariableLengthData const& theUserSuppliedTag,
                                       OrderType sentOrder,
                                       TransportationType theType,
                                       LogicalTime const& theTime,
                                       OrderType receivedOrder,
                                       MessageRetractionHandle theHandle,
                                       RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized,
                                                                                            InteractionParameterNotRecognized,
                                                                                            InteractionClassNotSubscribed,
                                                                                            InvalidLogicalTime,
                                                                                            FederateInternalError)
{
  std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;

  auto interaction = converter.to_bytes(theInteraction.toString());
  std::string tag = std::string((char*)theUserSuppliedTag.data(), theUserSuppliedTag.size());

  LOG_INFO("Interaction 6 handle=%s, tag=%s, parameterCount=%u", interaction.c_str(), tag.c_str(), theParameterValues.size());

  for (auto i = theParameterValues.begin(); i != theParameterValues.end(); i++)
  {
    std::string param = converter.to_bytes(i->first.toString());
    std::string value = std::string((char*)i->second.data(), i->second.size());
    LOG_INFO("paramHandle=%s, paramValue=%s", param.c_str(), value.c_str());
  }
  LOG_INFO("");
}

@method
void removeObjectInstance(ObjectInstanceHandle theObject,
                                         VariableLengthData const& theUserSuppliedTag,
                                         OrderType sentOrder) throw(ObjectInstanceNotKnown, FederateInternalError)
{
  LOG_INFO("Object Removed 1: handle= %ls", theObject.toString().c_str());
}

@method
void removeObjectInstance(ObjectInstanceHandle theObject,
                                         VariableLengthData const& theUserSuppliedTag,
                                         OrderType sentOrder,
                                         LogicalTime const& theTime,
                                         OrderType receivedOrder) throw(ObjectInstanceNotKnown, FederateInternalError)
{
  LOG_INFO("Object Removed 2: handle= %ls", theObject.toString().c_str());
}

@method
void removeObjectInstance(ObjectInstanceHandle theObject,
                                         VariableLengthData const& theUserSuppliedTag,
                                         OrderType sentOrder,
                                         LogicalTime const& theTime,
                                         OrderType receivedOrder,
                                         MessageRetractionHandle theHandle) throw(ObjectInstanceNotKnown,
                                                                                  InvalidLogicalTime, FederateInternalError)
{
  LOG_INFO("Object Removed 3: handle= %ls", theObject.toString().c_str());
}
