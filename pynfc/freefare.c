#include <openssl/des.h>

//HACK: ctypelib2 dosn't like enums
struct mifare_tag;
typedef struct mifare_tag *MifareTag;
int freefare_get_tag_type (MifareTag tag);

#include "freefare.h"

//HACK: We also need some of the interals:

#define MAX_CRYPTO_BLOCK_SIZE 16

#define MIFARE_ULTRALIGHT_PAGE_COUNT  0x10
#define MIFARE_ULTRALIGHT_C_PAGE_COUNT 0x30
#define MIFARE_ULTRALIGHT_C_PAGE_COUNT_READ 0x2C
// Max PAGE_COUNT of the Ultralight Family:
#define MIFARE_ULTRALIGHT_MAX_PAGE_COUNT 0x30

struct supported_tag {
    enum mifare_tag_type type;
    const char *friendly_name;
    uint8_t SAK;
    uint8_t ATS_min_length;
    uint8_t ATS_compare_length;
    uint8_t ATS[5];
    bool (*check_tag_on_reader) (nfc_device *, nfc_iso14443a_info);
};

/*
 * This structure is common to all supported MIFARE targets but shall not be
 * used directly (it's some kind of abstract class).  All members in this
 * structure are initialized by freefare_get_tags().
 *
 * Extra members in derived classes are initialized in the correpsonding
 * mifare_*_connect() function.
 */
struct mifare_tag {
    nfc_device *device;
    nfc_iso14443a_info info;
    const struct supported_tag *tag_info;
    int active;
};

struct mifare_classic_tag {
    struct mifare_tag __tag;

    MifareClassicKeyType last_authentication_key_type;

    /*
     * The following block numbers are on 2 bytes in order to use invalid
     * address and avoid false cache hit with inconsistent data.
     */
    struct {
      int16_t sector_trailer_block_number;
      uint16_t sector_access_bits;
      int16_t block_number;
      uint8_t block_access_bits;
    } cached_access_bits;
};

struct mifare_desfire_aid {
    uint8_t data[3];
};

enum mifare_desfire_key_type {
    T_DES,
    T_3DES,
    T_3K3DES,
    T_AES
};

struct mifare_desfire_key {
    uint8_t data[24];
    enum mifare_desfire_key_type type;
    DES_key_schedule ks1;
    DES_key_schedule ks2;
    DES_key_schedule ks3;
    uint8_t cmac_sk1[24];
    uint8_t cmac_sk2[24];
    uint8_t aes_version;
};

enum mifare_desfire_tag_authentication_scheme {
    AS_LEGACY,
    AS_NEW
};
struct mifare_desfire_tag {
    struct mifare_tag __tag;

    uint8_t last_picc_error;
    uint8_t last_internal_error;
    uint8_t last_pcd_error;
    MifareDESFireKey session_key;
    enum mifare_desfire_tag_authentication_scheme authentication_scheme;
    uint8_t authenticated_key_no;
    uint8_t ivect[MAX_CRYPTO_BLOCK_SIZE];
    uint8_t cmac[16];
    uint8_t *crypto_buffer;
    size_t crypto_buffer_size;
    uint32_t selected_application;
};

MifareDESFireKey mifare_desfire_session_key_new (uint8_t rnda[8], uint8_t rndb[8], MifareDESFireKey authentication_key);
const char	*mifare_desfire_error_lookup (uint8_t error);

struct mifare_ultralight_tag {
    struct mifare_tag __tag;

    /* mifare_ultralight_read() reads 4 pages at a time (wrapping) */
    MifareUltralightPage cache[MIFARE_ULTRALIGHT_MAX_PAGE_COUNT + 3];
    uint8_t cached_pages[MIFARE_ULTRALIGHT_MAX_PAGE_COUNT];
};

