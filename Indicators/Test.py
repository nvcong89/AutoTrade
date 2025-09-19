from Indicators import MomentumIndicators, Utils


sample_data = [
    [1846.4, 1846.5, 1846.0, 1846.1, 1090],
    [1846.2, 1846.6, 1846.1, 1826.3, 1200],
    [1846.2, 1846.6, 1846.1, 1846.3, 1200],
    [1846.2, 1846.6, 1846.1, 1886.3, 1200],
    [1846.2, 1846.6, 1846.1, 1816.3, 1200],
    [1846.2, 1846.6, 1846.1, 1826.3, 1200],
    [1846.2, 1846.6, 1846.1, 1866.3, 1200],
    [1846.2, 1846.6, 1846.1, 1896.3, 1200],
    [1846.2, 1846.6, 1846.1, 1816.3, 1200],
    [1846.2, 1846.6, 1846.1, 1836.3, 1200],
    [1846.2, 1846.6, 1846.1, 1876.3, 1200],
    [1846.2, 1846.6, 1846.1, 1866.3, 1200]
]

rsi_values = MomentumIndicators.rsi(sample_data, 8)
rsi2_values = MomentumIndicators.rsi(sample_data, 2)

check = Utils.cross(rsi_values,rsi2_values)


if check:
    print("đường 1 cắt lên đường 2")
else:
    print("Không cắt")

print(rsi_values)
print(rsi_values[-1])
print(rsi2_values[-1])