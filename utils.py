import uuid
import base64
from slugify import slugify


def generate_b64_uuid():
    uuid_bytes = uuid.uuid4().bytes
    b64_uuid = base64.urlsafe_b64encode(uuid_bytes).rstrip(b"=").decode("utf-8")
    return b64_uuid


def slugify_title(title) -> str:
    uuid_str = generate_b64_uuid()
    to_slug = f"{title}_{uuid_str}"
    return slugify(to_slug)


def test():
    # print(generate_b64_uuid())
    print(slugify_title("Test Title"))


if __name__ == "__main__":
    test()
