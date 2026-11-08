include_directories("${SS_PS4_ROOT}/platform/ps4/include" "${SS_PS4_ROOT}/build/ps4-usb")
# PS4 links the engine modules into one executable.
set_property(TARGET ${ENGINELIB} PROPERTY LINK_LIBRARIES engine_safemath${MP})
set_property(TARGET SeriousSam${MP} PROPERTY LINK_FLAGS "")
set(SS_NATIVE_STACK "/home/nichlas/Doom3-Ps4/build/native" CACHE PATH "Built native PS4 graphics stack")
set(vorbis_dir "${CMAKE_SOURCE_DIR}/External/libvorbis")
set(ogg_dir "${CMAKE_SOURCE_DIR}/External/libogg")
set(vorbis_sources analysis bitrate block codebook envelope floor0 floor1 info lookup
  lpc lsp mapping0 mdct psy registry res0 sharedbook smallft synthesis vorbisfile window)
list(TRANSFORM vorbis_sources PREPEND "${vorbis_dir}/lib/")
list(TRANSFORM vorbis_sources APPEND ".c")
add_library(ps4_vorbis STATIC ${vorbis_sources} "${ogg_dir}/src/bitwise.c" "${ogg_dir}/src/framing.c")
target_include_directories(ps4_vorbis PRIVATE "${vorbis_dir}/include" "${ogg_dir}/include")
add_custom_command(OUTPUT "${CMAKE_BINARY_DIR}/static_exports.cpp"
  COMMAND python3 "${SS_PS4_ROOT}/scripts/generate-static-exports.py"
    "${CMAKE_BINARY_DIR}/static_exports.cpp" "$<TARGET_FILE:${GAMEMPLIB}>" "$<TARGET_FILE:${ENTITIESMPLIB}>" "$<TARGET_FILE:${SHADERSLIB}>"
    "$<TARGET_FILE:amp11lib${MP}>" "$<TARGET_FILE:ps4_vorbis>"
  DEPENDS ${GAMEMPLIB} ${ENTITIESMPLIB} ${SHADERSLIB} amp11lib${MP} ps4_vorbis "${SS_PS4_ROOT}/scripts/generate-static-exports.py")
target_sources(SeriousSam${MP} PRIVATE "${CMAKE_BINARY_DIR}/static_exports.cpp"
  "${SS_PS4_ROOT}/platform/ps4/input.cpp"
  "${SS_PS4_ROOT}/platform/ps4/storage.cpp"
  "${SS_PS4_ROOT}/platform/ps4/videoout_wsi.cpp")
if(INTERNAL_NAME STREQUAL "serioussamse")
  target_compile_definitions(SeriousSam${MP} PRIVATE SS_PS4_TSE)
endif()
set_property(TARGET SeriousSam${MP} PROPERTY LINK_LIBRARIES
  "-Wl,--start-group" ${GAMEMPLIB} ${ENTITIESMPLIB} ${SHADERSLIB} ${ENGINELIB} engine_safemath${MP} amp11lib${MP} ps4_vorbis
  "${SS_PS4_ROOT}/build/ps4-sdl/libSDL2.a"
  "${SS_NATIVE_STACK}/vulkan-ps4/libvulkan_ps4.a"
  "${SS_NATIVE_STACK}/opengnm/libopengnm.a"
  "${SS_NATIVE_STACK}/libpsbc-private.a"
  "${SS_PS4_ROOT}/build/ps4-usb/libss-jbc.a"
  "-Wl,--end-group" SceGnmDriver)
