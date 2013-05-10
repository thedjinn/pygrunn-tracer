import math

class Vector(object):
    def __init__(self, x, y, z):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def __str__(self): return "(%s,%s,%s)" % (self.x, self.y, self.z)
    def __repr__(self): return "Vector" + str(self)
    def __add__(self, other): return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
    def __sub__(self, other): return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
    def __mul__(self, other): return Vector(self.x * other.x, self.y * other.y, self.z * other.z)

    def scalar_multiply(self, scalar): return Vector(scalar * self.x, scalar * self.y, scalar * self.z)

    def dot(self, other): return self.x * other.x + self.y * other.y + self.z * other.z
    def cross(self, other): return Vector(self.y * other.z - self.z * other.y, self.z * other.x - self.x * other.z, self.x * other.y - self.y * other.x)

    def normalized(self): return self.scalar_multiply(1.0 / math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z))

    def reflect(self, normal):
        d = normal.scalar_multiply(self.dot(normal))
        return self - d.scalar_multiply(2.0)

class Material(object):
    def __init__(self, reflectiveness, diffuse_color):
        self.reflectiveness = reflectiveness
        self.diffuse_color = diffuse_color

class Light(object):
    def __init__(self, origin, color):
        self.origin = origin
        self.color = color

class Ray(object):
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction

class Intersection(object):
    def __init__(self, point, distance, normal, obj):
        self.point = point
        self.distance = distance
        self.normal = normal
        self.object = obj

class Sphere(object):
    def __init__(self, origin, radius, material):
        self.origin = origin
        self.radius = radius
        self.material = material

    def intersect(self, ray, max_distance):
        v = self.origin - ray.origin
        v_dot_direction = v.dot(ray.direction)

        discriminant = v_dot_direction * v_dot_direction - v.dot(v) + self.radius * self.radius

        if discriminant < 0:
            return None # no intersections

        discriminant = math.sqrt(discriminant)

        t1 = v_dot_direction + discriminant
        if t1 < 0:
            return None # no intersections

        t2 = v_dot_direction - discriminant
        if t2 > max_distance:
            return None # too far away

        if t2 < 0:
            t = t1
        else:
            t = min(t1, t2)

        point = ray.origin + ray.direction.scalar_multiply(t)
        normal = (point - self.origin).normalized()

        return Intersection(point, t, normal, self)

class Plane(object):
    def __init__(self, origin, normal, material):
        self.origin = origin
        self.normal = normal
        self.material = material

    def intersect(self, ray, max_distance):
        denom = ray.direction.dot(self.normal)

        if denom != 0:
            distance = (self.origin - ray.origin).dot(self.normal) / denom
            if distance > 0 and distance < max_distance:
                point = ray.origin + ray.direction.scalar_multiply(distance)
                return Intersection(point, distance, self.normal, self)

        return None # direction and normal are parallel or too far away

class Tracer(object):
    def __init__(self):
        red = Vector(1, 0, 0)
        blue = Vector(0, 0, 1)
        green = Vector(0, 1, 0)
        white = Vector(1, 1, 1)

        chrome = Material(0.5, Vector(1.0, 1.0, 1.0))
        red_surface = Material(0.0, Vector(1.0, 0.5, 0.5))
        green_surface = Material(0.0, Vector(0.5, 1.0, 0.5))

        origin = Vector(20.0, 0.0, 100.0)
        lookat = Vector(0, 20, 200)
        self.eye = Ray(origin, (lookat - origin).normalized())
        self.fov = math.pi / 4 # 45 degrees

        self.lights = [
            Light(Vector(-100, -100, 200), Vector(0.5, 0.5, 0.5)),
            Light(Vector( 100, -50,  100), Vector(0.5, 0.5, 0.5))
        ]

        self.objects = [
            Sphere(Vector(-40,  60, 200), 20.0, chrome),
            Sphere(Vector(0, 40,  240), 40.0, chrome),
            Sphere(Vector(40,  60, 200), 20.0, chrome),
            Plane(Vector(0, 80, 0), Vector(0, -1, 0), red_surface),
            Plane(Vector(0, -180, 0), Vector(0, 1, 0), red_surface),
            Plane(Vector(-200, 0, 0), Vector(1, 0, 0), green_surface),
            Plane(Vector(200, 0, 0), Vector(-1, 0, 0), green_surface),
            Plane(Vector(0, 0, 600), Vector(0, 0, -1), green_surface),
            Plane(Vector(0, 0, -600), Vector(0, 0, 1), green_surface)
        ]

    def find_nearest_intersection(self, ray):
        max_distance = 1e6
        result = None

        for obj in self.objects:
            intersection = obj.intersect(ray, max_distance)

            if intersection:
                result = intersection
                max_distance = intersection.distance

        return result

    def find_lights(self, intersection):
        lights = []

        for light in self.lights:
            i = self.find_nearest_intersection(Ray(light.origin, (intersection.point - light.origin).normalized()))
            if i and i.object is intersection.object:
                lights.append(light)

        return lights

    def trace_lights(self, intersection):
        attenuation = Vector(0, 0, 0)

        for light in self.lights:
            light_direction = (light.origin - intersection.point).normalized()

            i = self.find_nearest_intersection(Ray(light.origin, light_direction.scalar_multiply(-1)))
            if not i:
                continue

            if i.object is intersection.object:
                factor = intersection.normal.dot(light_direction)
                if factor > 0:
                    specular = light.color.scalar_multiply(factor ** 40)
                    attenuation += light.color.scalar_multiply(factor) + specular

        return intersection.object.material.diffuse_color * attenuation

    def trace(self, ray, influence):
        color = Vector(0, 0, 0)

        # Do not reflect to infinity
        if influence < 0.1:
            return color

        intersection = self.find_nearest_intersection(ray)
        if intersection:
            color = self.trace_lights(intersection)

            # Add reflection
            material = intersection.object.material
            if material.reflectiveness > 0:
                direction = ray.direction.reflect(intersection.normal)
                color = color.scalar_multiply(1.0 - intersection.object.material.reflectiveness) + self.trace(Ray(intersection.point + direction.scalar_multiply(0.0001), direction), influence * intersection.object.material.reflectiveness).scalar_multiply(intersection.object.material.reflectiveness)

        return color

    def pixels(self, width, height):
        half_width = math.tan(self.fov)
        half_height = (float(height) / float(width)) * half_width

        pixel_width = (half_width * 2.0) / (width - 1.0)
        pixel_height = (half_height * 2.0) / (height - 1.0)

        right = self.eye.direction.cross(Vector(0.0, 1.0, 0.0)).normalized()
        up = right.cross(self.eye.direction).normalized()

        for y in xrange(height):
            for x in xrange(width):
                color = Vector(0.0, 0.0, 0.0)

                for yy in xrange(-2, 3):
                    for xx in xrange(-2, 3):
                        xcomp = right.scalar_multiply((x + xx * 0.25) * pixel_width - half_width)
                        ycomp = up.scalar_multiply((y + yy * 0.25) * pixel_height - half_height)
                        ray = Ray(self.eye.origin, (self.eye.direction + xcomp + ycomp).normalized())

                        color += self.trace(ray, 1.0)

                yield color.scalar_multiply(1.0 / 25)

def write_ppm(filename, width, height, pixels):
    with open(filename, 'wb') as f:
        f.write('P6 %d %d 255\n' % (width, height))
        for pixel in pixels:
            f.write(chr(min(int(pixel.x * 255.0), 255)) + chr(min(int(pixel.y * 255.0), 255)) + chr(min(int(pixel.z * 255.0), 255)))

width, height = 1024, 768
tracer = Tracer()

write_ppm("output.ppm", width, height, tracer.pixels(width, height))
