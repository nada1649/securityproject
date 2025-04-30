% Clear environment
clc; clear; close all;
pkg load control
pkg load communications
pkg load image

% --- Custom upsample function ---
function y = upsample_manual(x, n)
  y = zeros(1, n * length(x));
  y(1:n:end) = x;
end

% --- Define the signal g(n) ---
g = [5 4 3 2 1] / sqrt(55);

% --- Define filters ---
h_matched = fliplr(g);            % Matched filter
h_impulse = [1];                  % Impulse response
h_rect = ones(1, 5) / sqrt(5);    % Rect filter with unity energy

% --- BER Calculation with 100,000 bits ---
N = 100000;
Ts = 5;
num_bits = ceil(N / Ts);
bits = 2 * randi([0 1], 1, num_bits) - 1; % This transforms 0's and 1's into -1's and 1's

signal = upsample_manual(bits, Ts);
signal = signal(1:N);  % Trim to 100k samples

% Transmit through channel (convolve with g)
y_clean = conv(signal, g);

% Add AWGN with SNR = 0 dB
y_noisy = awgn(y_clean, 0, 'measured');

% --- Function to compute BER ---
function ber = compute_BER(y_noisy, filter, bits, Ts)
    y_filtered = conv(y_noisy, filter); % Filter y by convolving with filter
    start_index = length(filter); % Start index is the delay introduced by the filter to start taking the first sample
    sampling_indices = start_index:Ts:length(y_filtered);  % In this case Ts = 5 so we start at the delay then take sample every 5 bits

    % Ensure we don't access out-of-bounds bits
    max_valid_samples = min(length(sampling_indices), length(bits));
    sampling_indices = sampling_indices(1:max_valid_samples);

    samples = y_filtered(sampling_indices); % Take samples every sampling index
    original_bits = bits(1:max_valid_samples);
    received_bits = samples > 0;  % Transforms array to 0's and 1's again (logical array)

    num_errors = sum(received_bits ~= (original_bits > 0)); % XOR's the original bits with received bits and counts the 1's (differences)
    ber = num_errors / max_valid_samples;  % Num of errors / Total num of bits
end


% Calculate BERs
ber_matched = compute_BER(y_noisy, h_matched, bits, Ts);
ber_impulse = compute_BER(y_noisy, h_impulse, bits, Ts);
ber_rect = compute_BER(y_noisy, h_rect, bits, Ts);

% Print Results
fprintf("BER with matched filter: %.4f\n", ber_matched);
fprintf("BER with impulse filter: %.4f\n", ber_impulse);
fprintf("BER with rect filter   : %.4f\n", ber_rect);

% --- Theoretical vs Simulated BER Plot ---
SNRs = -10:1:10;

% Creates arrays with size of SNRs array (to store value of each filter for every SNR)
sim_ber_matched = zeros(1, length(SNRs));
sim_ber_impulse = zeros(1, length(SNRs));
sim_ber_rect = zeros(1, length(SNRs));

% Compute BERs for different SNR values
for i = 1:length(SNRs)
    y_noisy_loop = awgn(y_clean, SNRs(i), 'measured'); % Adds Additive White Gaussian Noise to te clean signal

    % Calculates the experimental BER for each array
    sim_ber_matched(i) = compute_BER(y_noisy_loop, h_matched, bits, Ts);
    sim_ber_impulse(i) = compute_BER(y_noisy_loop, h_impulse, bits, Ts);
    sim_ber_rect(i)   = compute_BER(y_noisy_loop, h_rect, bits, Ts);
end

% Theoretical BERs
BER_theo_A = qfunc(sqrt(2 .* 10.^(SNRs / 10)));                      % Matched
BER_theo_B = qfunc(sqrt((2 / 55) .* 10.^(SNRs / 10)));               % Impulse
BER_theo_C = qfunc((3 / 11) .* sqrt(22 .* 10.^(SNRs / 10)));         % Rect

% --- Plot for Matched Filter ---
figure;
semilogy(SNRs, sim_ber_matched, 'o-', 'LineWidth', 1.5); hold on;
semilogy(SNRs, BER_theo_A, '--', 'LineWidth', 1.5);
xlabel('E/No (dB)');
ylabel('Bit Error Rate (BER)');
title('Theoretical vs Simulated BER for Matched Filter');
legend({'Simulated BER', 'Theoretical BER'}, 'Location', 'SouthWest');
grid on;

% --- Plot for Impulse Filter ---
figure;
semilogy(SNRs, sim_ber_impulse, 's-', 'LineWidth', 1.5); hold on;
semilogy(SNRs, BER_theo_B, '--', 'LineWidth', 1.5);
xlabel('E/No (dB)');
ylabel('Bit Error Rate (BER)');
title('Theoretical vs Simulated BER for Impulse Filter');
legend({'Simulated BER', 'Theoretical BER'}, 'Location', 'SouthWest');
grid on;

% --- Plot for Rect Filter ---
figure;
semilogy(SNRs, sim_ber_rect, 'd-', 'LineWidth', 1.5); hold on;
semilogy(SNRs, BER_theo_C, '--', 'LineWidth', 1.5);
xlabel('E/No (dB)');
ylabel('Bit Error Rate (BER)');
title('Theoretical vs Simulated BER for Rect Filter');
legend({'Simulated BER', 'Theoretical BER'}, 'Location', 'SouthWest');
grid on;

% --- Combined Plot for All Filters ---
figure;
semilogy(SNRs, sim_ber_matched, 'o-', 'LineWidth', 1.5); hold on;
semilogy(SNRs, sim_ber_impulse, 's-', 'LineWidth', 1.5);
semilogy(SNRs, sim_ber_rect, 'd-', 'LineWidth', 1.5);

semilogy(SNRs, BER_theo_A, '--', 'LineWidth', 1.5);
semilogy(SNRs, BER_theo_B, '--', 'LineWidth', 1.5);
semilogy(SNRs, BER_theo_C, '--', 'LineWidth', 1.5);

xlabel('E/No (dB)');
ylabel('Bit Error Rate (BER)');
title('Theoretical vs Simulated BER for All Filters');
legend({'Simulated Matched', 'Simulated Impulse', 'Simulated Rect', ...
        'Theoretical Matched', 'Theoretical Impulse', 'Theoretical Rect'}, ...
        'Location', 'SouthWest');
grid on;

% --- 3-bit example for visualization ---
bits3 = 2 * randi([0 1], 1, 3) - 1; % Creates 3 random bits that are either 1 or -1
signal3 = upsample_manual(bits3, 5);
signal3 = signal3(1:length(bits3) * 5);

y_clean3 = conv(signal3, g); % Convolve the g with the 3 bits to get a train of g's (+ve and -ve)
y_noisy3 = awgn(y_clean3, 5, 'measured'); % Adds Noise with SNR = 5dB

% Passes noisy signal through each filter
y_noisy_matched = conv(y_noisy3, h_matched);
y_noisy_impulse = conv(y_noisy3, h_impulse);
y_noisy_rect = conv(y_noisy3, h_rect);

% Plotting
figure;
subplot(4,1,1);
plot(y_clean3, 'LineWidth', 1.5); grid on;
title('Signal without Noise');

subplot(4,1,2);
plot(y_noisy_matched, 'LineWidth', 1.5); grid on;
title('Signal with Noise (Matched Filter)');

subplot(4,1,3);
plot(y_noisy_impulse, 'LineWidth', 1.5); grid on;
title('Signal with Noise (Impulse Filter)');

subplot(4,1,4);
plot(y_noisy_rect, 'LineWidth', 1.5); grid on;
title('Signal with Noise (Rect Filter)');

% Define input images and SNR values
image_files = {'image1.png', 'image2.png', 'image3.png'};
SNRs = [-10, -5, 0, 5];
target_size = [200, 200];  % Resize all images to this size

% Pulse shaping parameters
delay = length(h_matched) - 1;

for snr_idx = 1:length(SNRs)
    SNR = SNRs(snr_idx);  % Current SNR
    fprintf('Processing for SNR = %d dB\n', SNR);

    figure;

    for i = 1:length(image_files)
        % Load image from file
        img = imread(image_files{i});

        % If the image is grayscale (2D), replicate channels to convert to RGB (3D)
        if size(img, 3) == 1
            img = cat(3, img, img, img);  % Convert grayscale to RGB
        end

        img = imresize(img, target_size); % Resize the image to the target size to make processing easier

        received_img = zeros(size(img), 'uint8'); % We will store received img here (uint8 because we store 8 bits because each pixel is 8 bits)

        % Process each of the 3 RGB color channels separately
        for channel = 1:3
            channel_data = img(:,:,channel);  % Extract current channel

            bits = reshape(de2bi(channel_data(:), 8, 'left-msb')', 1, []);  % Convert pixel values (0–255) to binary bitstream (8 bits per pixel)

            pam_signal = 2 * bits - 1; % Map binary bits {0,1} to PAM symbols {-1, +1}

            y_img_clean = conv(upsample_manual(pam_signal, 8), g); % Upsample and pulse shape using convolution with transmit filter `g`

            y_img_noisy = awgn(y_img_clean, SNR, 'measured'); % Add white Gaussian noise to the clean signal

            filtered_signal = conv(y_img_noisy, h_matched); % Apply matched filter

            % Sample the filtered signal at symbol intervals (with delay)
            sample_indices = delay + 1 : 8 : delay + length(bits) * 8;
            sampled_bits = filtered_signal(sample_indices) > 0;  % Transforms array to 0's and 1's again (logical array)

            % Reshape bitstream back into 8-bit integers (bytes)
            reshaped_bits = reshape(sampled_bits, 8, [])';
            decoded_vals = bi2de(reshaped_bits, 'left-msb');  % Convert bits to pixel values

            % Reshape flat vector back to 2D image matrix
            channel_received = reshape(decoded_vals, target_size);

            % Store received channel into the final image
            received_img(:,:,channel) = uint8(channel_received);
        end

        % Display the original image in a subplot
        subplot(length(image_files), 2, (i - 1)*2 + 1);
        imshow(img);
        title(sprintf('Original Image %d', i));

        % Display the received (noisy and decoded) image in a subplot
        subplot(length(image_files), 2, (i - 1)*2 + 2);
        imshow(received_img);
        title(sprintf('Received Image %d (SNR: %d dB)', i, SNR));
    end
end
