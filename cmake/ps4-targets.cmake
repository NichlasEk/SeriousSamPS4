include_directories("${SS_PS4_ROOT}/platform/ps4/include")
# PS4 links the engine modules into one executable.
set_property(TARGET Engine PROPERTY LINK_LIBRARIES engine_safemath)
set_property(TARGET SeriousSam PROPERTY LINK_FLAGS "")
set(SS_NATIVE_STACK "/home/nichlas/Doom3-Ps4/build/native" CACHE PATH "Built native PS4 graphics stack")
add_custom_command(OUTPUT "${CMAKE_BINARY_DIR}/static_exports.cpp"
  COMMAND python3 "${SS_PS4_ROOT}/scripts/generate-static-exports.py"
    "${CMAKE_BINARY_DIR}/static_exports.cpp" "$<TARGET_FILE:Game>" "$<TARGET_FILE:Entities>" "$<TARGET_FILE:Shaders>"
  DEPENDS Game Entities Shaders "${SS_PS4_ROOT}/scripts/generate-static-exports.py")
target_sources(SeriousSam PRIVATE "${CMAKE_BINARY_DIR}/static_exports.cpp"
  "${SS_PS4_ROOT}/platform/ps4/videoout_wsi.cpp")
set_property(TARGET SeriousSam PROPERTY LINK_LIBRARIES
  "-Wl,--start-group" Game Entities Shaders Engine engine_safemath
  "${SS_PS4_ROOT}/build/ps4-sdl/libSDL2.a"
  "${SS_NATIVE_STACK}/vulkan-ps4/libvulkan_ps4.a"
  "${SS_NATIVE_STACK}/opengnm/libopengnm.a"
  "${SS_NATIVE_STACK}/libpsbc-private.a"
  "-Wl,--end-group" SceGnmDriver)
