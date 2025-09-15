cmake_minimum_required(VERSION 3.12)
project(vrp_solver LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(vrp_solver vrp_solver.cpp)

