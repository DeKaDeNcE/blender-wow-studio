//
// Created by cromon on 06.05.2018.
//

#include <stdexcept>
#include <cstring>
#include "ByteStream.h"

namespace python_blp {
    ByteStream::ByteStream(unsigned char *bytes, std::size_t size) : data(bytes), size(size), position(0) {

    }

    ByteStream::ByteStream(python_blp::ByteStream &&other) noexcept {
        data = other.data;
        size = other.size;
        position = other.position;
        other.data = nullptr;
        other.size = other.position = 0;
    }

    ByteStream &ByteStream::operator=(ByteStream &&other) noexcept {
        data = other.data;
        size = other.size;
        position = other.position;
        other.data = nullptr;
        other.size = other.position = 0;
        return *this;
    }

    void ByteStream::read(void *buffer, std::size_t numBytes) {
        if(position + numBytes > size) {
            throw std::out_of_range("Cannot read past the end of stream");
        }

        memcpy(buffer, data + position, numBytes);
        position += numBytes;
    }
}