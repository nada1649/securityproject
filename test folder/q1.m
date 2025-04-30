% Parameters
A = 5;         % Amplitude
T = 1;         % Bit duration
k = 1;         % Constant for matched filter
bit_seq = [0 1 1];

% Time resolution
dt = 0.001;
t = 0:dt:(length(bit_seq)*T - dt);

% Generate original signal
signal = zeros(size(t));
for i = 1:length(bit_seq)
    idx = (t >= (i-1)*T) & (t < i*T);
    if bit_seq(i) == 1
        signal(idx) = A;
    else
        signal(idx) = -A;
    end
end

% Create matched filter h(t) = k * S(T - t)
t_filter = 0:dt:T-dt;
pulse = A * ones(size(t_filter));
matched_filter = k * fliplr(pulse);

% Convolution (matched filtering)
filtered_output = conv(signal, matched_filter) * dt;
t_conv = 0:dt:(length(filtered_output)-1)*dt;

% Sampling times (at end of each bit)
sampling_times = T:T:(length(bit_seq)*T);
[~, sample_indices] = min(abs(t_conv' - sampling_times), [], 1);
sample_values = filtered_output(sample_indices);

% Plotting
figure;

subplot(3,1,1);
plot(t, signal, 'LineWidth', 2);
title('Original Signal (Bit Sequence 0 1 1)');
xlabel('Time (s)');
ylabel('Amplitude');
ylim([-A*1.5, A*1.5]);
grid on;

subplot(3,1,2);
plot(t_filter, matched_filter, 'r', 'LineWidth', 2);
title('Matched Filter h(t) = k·S(T - t)');
xlabel('Time (s)');
ylabel('Amplitude');
grid on;

subplot(3,1,3);
plot(t_conv, filtered_output, 'k', 'LineWidth', 2); hold on;
stem(sampling_times, sample_values, 'r', 'filled', 'LineWidth', 1.5);
for i = 1:length(sampling_times)
    xline(sampling_times(i), '--b');
end
title('Matched Filter Output with Sampling Times');
xlabel('Time (s)');
ylabel('Amplitude');
legend('Convolution Output', 'Sampled Values', 'Sampling Times');
grid on;

