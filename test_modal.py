import modal

FaceService = modal.Cls.from_name("face-gpu", "FaceService")
f = FaceService.embed

with open("test.jpg", "rb") as img:
    result = f.remote(img.read())

print(type(result))
print(result[:5] if isinstance(result, list) else result)
