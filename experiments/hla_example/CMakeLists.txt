cmake_minimum_required(VERSION 3.5.1)

include(GNUInstallDirs)
include(CMakePrintHelpers)

file(GLOB SOURCES "Example*.cpp")

cmake_print_variables(SOURCES)
cmake_print_variables(PROJECT_NAME)
cmake_print_variables(PROJECT_SOURCE_DIR)

include_directories(${PROJECT_SOURCE_DIR}/install/include/rti1516)
link_directories(${PROJECT_SOURCE_DIR}/install/lib)

add_executable(${PROJECT_NAME} main.cpp ${SOURCES})
set_target_properties(${PROJECT_NAME} PROPERTIES VERSION ${PROJECT_VERSION})

# add_library(${PROJECT_NAME}-lib ExampleFedAmb.cpp ExampleCPPFederate.cpp)

target_link_libraries(${PROJECT_NAME} libcpphelpers)
target_link_libraries(${PROJECT_NAME} rti1516 fedtime1516)

