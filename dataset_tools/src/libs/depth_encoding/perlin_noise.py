import numpy as np
import cv2
from noise import perlin
from itertools import product


def generate_perlin_noise(image_shape):
    pn = perlin.SimplexNoise()
    pn.randomize()
    img = map(
        lambda p: pn.noise2(p[0], p[1]),
        product(range(image_shape[1]), range(image_shape[0])))
    img = np.array(list(img)).reshape(image_shape)
    return img


def smoothen_noise(noise_factor, x, y):
    image_shape = noise_factor.shape
    fracX = x - int(x)
    fracY = y - int(y)
    x1 = (int(x) + image_shape[1]) % image_shape[1]
    y1 = (int(y) + image_shape[0]) % image_shape[0]

    x2 = (x1 + image_shape[1] - 1) % image_shape[1]
    y2 = (y1 + image_shape[0] - 1) % image_shape[0]

    value = 0
    value += fracX * fracY * noise_factor[y1][x1]
    value += (1 - fracX) * fracY * noise_factor[y1][x2]
    value += fracX * (1 - fracY) * noise_factor[y2][x1]
    value += (1 - fracX) * (1 - fracY) * noise_factor[y2][x2]
    return value


def zoom_in(noise_factor, scale=8, thresh=0):
    image_shape = noise_factor.shape
    img = map(
        lambda p: noise_factor[p[0] // scale][p[1] // scale],
        product(range(image_shape[1]), range(image_shape[0])))

    img = np.array(list(img)).reshape(image_shape)
    return img


def smooth_zoom(noise_factor, scale=8, thresh=0):
    image_shape = noise_factor.shape
    img = map(
        lambda p: smoothen_noise(noise_factor, p[1] / scale, p[0] / scale),
        product(range(image_shape[1]), range(image_shape[0])))

    img = np.array(list(img)).reshape(image_shape)

    return img


def turbulence(noise_factor, scale=8, step=4):
    init_scale = scale
    image_shape = noise_factor.shape
    img = np.zeros(image_shape, np.float)
    loop_scale = init_scale
    while loop_scale >= 3:
        smooth_img = smooth_zoom(noise_factor, loop_scale)
        img += (smooth_img + 1) * loop_scale
        loop_scale //= step

    if init_scale > 4:
        loop_scale = 4
        zoom_img = zoom_in(noise_factor, loop_scale)
        img += (zoom_img + 1) * loop_scale

    return 128 * (img / init_scale)


def rand_turbulence(noise_factor, thresh_small, thresh_large, step):
    img4 = np.zeros(noise_factor.shape, np.uint8)
    img16 = img4.copy()
    if thresh_small > 0:
        img4 = turbulence(noise_factor, scale=4, step=step).astype(np.uint8)
        _, img4 = cv2.threshold(img4, thresh_small, 255, cv2.THRESH_BINARY)
    if thresh_large > 0:
        img16 = turbulence(noise_factor, scale=16, step=step).astype(np.uint8)
        _, img16 = cv2.threshold(img16, thresh_large, 255, cv2.THRESH_BINARY)
    img = cv2.bitwise_xor(img4, img16)
    return img


def perlin_noisy():
    pass


def gen_perlin_noisy_img(image_shape, thresh_small, thresh_large, step):
    noise_factor = generate_perlin_noise(image_shape)
    img = rand_turbulence(noise_factor, thresh_small, thresh_large, step)
    return img


def generate_gauss_noise(image_shape, var):
    sigma = var ** 0.5
    gauss = np.random.normal(0, sigma, image_shape)
    return gauss


def gauss_noisy(image_shape):
    img = np.zeros(image_shape, np.float)
    for var in np.arange(0.7, 0.8, 0.1):
        gauss = generate_gauss_noise(image_shape, var)
        init_scale = 32
        scale = init_scale
        while scale >= 3:
            img += smooth_zoom(gauss, scale) * scale
            scale //= 32
    return img.astype(np.uint8)


if __name__ == '__main__':
    img = np.zeros((500, 500), np.uint8)

    img = generate_perlin_noise(img.shape)
    cv2.imshow('img', img)
    cv2.circle(img, (200, 200), 100, 255, cv2.FILLED, cv2.LINE_8)
    print(np.where(img > 0))

    # sparse little black spots
    perlin_noise_img = gen_perlin_noisy_img(img.shape, 0, 50, 8)
    print(perlin_noise_img.shape)
    img = cv2.bitwise_xor(img, perlin_noise_img)
    cv2.imshow('black spots', perlin_noise_img)

    # dense little black dots
    perlin_noise_img = perlin_noisy(img.shape, 30, 0, 4)
    print(perlin_noise_img.shape)
    img = cv2.bitwise_xor(img, perlin_noise_img)
    cv2.imshow('black dots', perlin_noise_img)

    # dense white spots
    perlin_noise_img = perlin_noisy(img.shape, 0, 100, 4)
    print(perlin_noise_img.shape)
    img = cv2.bitwise_xor(img, perlin_noise_img)
    cv2.imshow('white spots', perlin_noise_img)

    # dense white dots
    perlin_noise_img = perlin_noisy(img.shape, 220, 0, 4)
    print(perlin_noise_img.shape)
    img = cv2.bitwise_xor(img, perlin_noise_img)
    cv2.imshow('white dots', perlin_noise_img)

    cv2.waitKey(0)
